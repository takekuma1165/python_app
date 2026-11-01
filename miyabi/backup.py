"""Versioned logical SQLite backups. Never execute SQL from an uploaded file."""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import os
import tempfile
import uuid

from miyabi.database import ArticleStore, FIELDS, now
from miyabi.publication import validate_pack
from miyabi.settings import validate_settings

MAX_BYTES = 32 * 1024 * 1024


def payload_from_connection(conn):
    articles = [dict(row) for row in conn.execute("SELECT * FROM articles ORDER BY id")]
    packs = [{"article_id": row["article_id"], "data": json.loads(row["data_json"]),
              "source_updated_at": row["source_updated_at"], "updated_at": row["updated_at"]}
             for row in conn.execute("SELECT * FROM publication_packs ORDER BY article_id")]
    settings = conn.execute("SELECT * FROM app_settings WHERE id=1").fetchone()
    return {"articles": articles, "publications": packs,
            "settings": None if settings is None else {"data": json.loads(settings["data_json"]), "updated_at": settings["updated_at"]}}


def snapshot(store):
    with store.connection() as conn:
        conn.execute("BEGIN")
        return payload_from_connection(conn)


def fingerprint(payload):
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def encode_backup(payload):
    return json.dumps({"format": "miyabi-studio-backup", "version": 1, "exported_at": now(), "payload": payload},
                      ensure_ascii=False, indent=2).encode("utf-8")


def backup_bytes(store):
    raw = encode_backup(snapshot(store))
    if len(raw) > MAX_BYTES:
        raise ValueError("バックアップは32MBまでです。アプリ停止後にSQLiteファイルを手動でコピーしてください。")
    return raw


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("日時の形式が正しくありません。")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError("日時の形式が正しくありません。") from None
    if parsed.tzinfo is None:
        raise ValueError("日時のタイムゾーンがありません。")


def validate_backup(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise ValueError("バックアップは32MB以内のJSONファイルを指定してください。")
    try:
        document = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(document, dict) or set(document) != {"format", "version", "exported_at", "payload"} or document["format"] != "miyabi-studio-backup" or type(document["version"]) is not int or document["version"] != 1:
            raise ValueError("対応していないバックアップ形式です。")
        timestamp(document["exported_at"])
        payload = document["payload"]
        if not isinstance(payload, dict) or set(payload) != {"articles", "publications", "settings"}:
            raise ValueError("バックアップの項目が正しくありません。")
        articles, packs = payload["articles"], payload["publications"]
        if not isinstance(articles, list) or not isinstance(packs, list) or len(articles) > 10000 or len(packs) > 10000:
            raise ValueError("バックアップの記事数が正しくありません（最大10000件）。")
        ids, pack_ids = set(), set()
        # Validate article business rules against a temporary database, not the live one.
        with tempfile.TemporaryDirectory() as directory:
            check = ArticleStore(Path(directory) / "check.sqlite3")
            for article in articles:
                if not isinstance(article, dict) or set(article) != {"id", "created_at", "updated_at", *FIELDS}:
                    raise ValueError("記事の項目が正しくありません。")
                article_id = article["id"]
                if type(article_id) is not int or not 1 <= article_id < 2**63 or article_id in ids:
                    raise ValueError("記事IDが正しくありません。")
                ids.add(article_id)
                timestamp(article["created_at"]); timestamp(article["updated_at"])
                if any(not isinstance(article[k], str) or len(article[k]) > 1000000 for k in FIELDS):
                    raise ValueError("記事の文字データが正しくありません。")
                check.save({k: article[k] for k in FIELDS})
        for pack in packs:
            if not isinstance(pack, dict) or set(pack) != {"article_id", "data", "source_updated_at", "updated_at"}:
                raise ValueError("投稿準備の項目が正しくありません。")
            article_id = pack["article_id"]
            if type(article_id) is not int or article_id not in ids or article_id in pack_ids:
                raise ValueError("投稿準備の記事IDが正しくありません。")
            pack_ids.add(article_id)
            validate_pack(pack["data"])
            timestamp(pack["source_updated_at"]); timestamp(pack["updated_at"])
        settings = payload["settings"]
        if settings is not None:
            if not isinstance(settings, dict) or set(settings) != {"data", "updated_at"}:
                raise ValueError("設定の項目が正しくありません。")
            validate_settings(settings["data"]); timestamp(settings["updated_at"])
        return payload
    except (UnicodeError, json.JSONDecodeError, TypeError, KeyError, OverflowError, RecursionError):
        raise ValueError("バックアップを読み取れませんでした。ファイル形式と内容を確認してください。") from None


def restore_backup(store, raw, expected_fingerprint):
    payload = validate_backup(raw)  # Complete validation before opening the live write transaction.
    safety = None
    with store.connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        previous = payload_from_connection(conn)
        if fingerprint(previous) != expected_fingerprint:
            raise ValueError("復元確認後にデータが変更されました。内容を確認し直してください。")
        folder = store.path.parent / "backups"
        folder.mkdir(parents=True, exist_ok=True)
        safety = folder / f"before-restore-{uuid.uuid4().hex}.json"
        safety_bytes = encode_backup(previous)
        if len(safety_bytes) > MAX_BYTES:
            raise ValueError("復元前データが32MBを超えるため、手動バックアップで対応してください。")
        with safety.open("xb") as stream:
            stream.write(safety_bytes); stream.flush(); os.fsync(stream.fileno())
        conn.execute("DELETE FROM publication_packs")
        conn.execute("DELETE FROM articles")
        conn.execute("DELETE FROM app_settings")
        versions, original_versions = {}, {}
        for article in payload["articles"]:
            # Fresh update stamps invalidate drafts in other open browser sessions.
            versions[article["id"]] = now()
            original_versions[article["id"]] = article["updated_at"]
            columns = ("id", "created_at", "updated_at", *FIELDS)
            values = [article[k] if k != "updated_at" else versions[article["id"]] for k in columns]
            conn.execute(f"INSERT INTO articles ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})", values)
        for pack in payload["publications"]:
            i = pack["article_id"]
            source = versions[i] if pack["source_updated_at"] == original_versions[i] else pack["source_updated_at"]
            conn.execute("INSERT INTO publication_packs VALUES (?,?,?,?)", (i, json.dumps(pack["data"], ensure_ascii=False), source, now()))
        if payload["settings"] is not None:
            conn.execute("INSERT INTO app_settings VALUES (1,?,?)", (json.dumps(payload["settings"]["data"], ensure_ascii=False), now()))
    return safety
