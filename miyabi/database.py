"""SQLite persistence. Connections are short-lived and writes are transactional."""
from __future__ import annotations

import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

STATUSES = ("アイデア", "構成中", "執筆中", "校正中", "完成", "公開済み")
GENRES = (
    "暮らしを整える", "人生の見直し", "新しい挑戦", "人間関係・家族",
    "健康と美容", "お金とこれからの生活", "自分らしい生き方", "数秘術を通じた自己理解",
)
FIELDS = (
    "title", "genre", "audience", "keyword", "search_intent", "outline", "body",
    "hashtags", "status", "published_on", "note_url", "notes",
)


def now() -> str:
    return datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="microseconds")


def empty_article() -> dict:
    return dict.fromkeys(FIELDS, "") | {
        "genre": GENRES[0], "audience": "40代・50代・60代以上の女性", "status": STATUSES[0],
    }


class ConflictError(ValueError):
    """The article changed in another session; do not silently overwrite it."""


class ArticleStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    genre TEXT NOT NULL DEFAULT '',
                    audience TEXT NOT NULL DEFAULT '',
                    keyword TEXT NOT NULL DEFAULT '',
                    search_intent TEXT NOT NULL DEFAULT '',
                    outline TEXT NOT NULL DEFAULT '',
                    body TEXT NOT NULL DEFAULT '',
                    hashtags TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL CHECK(status IN
                        ('アイデア','構成中','執筆中','校正中','完成','公開済み')),
                    published_on TEXT NOT NULL DEFAULT '',
                    note_url TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT ''
                )
            """)


            conn.execute("""CREATE TABLE IF NOT EXISTS publication_packs (
                article_id INTEGER PRIMARY KEY REFERENCES articles(id) ON DELETE CASCADE,
                data_json TEXT NOT NULL, source_updated_at TEXT NOT NULL, updated_at TEXT NOT NULL
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS app_settings (
                id INTEGER PRIMARY KEY CHECK(id=1), data_json TEXT NOT NULL, updated_at TEXT NOT NULL
            )""")

    def settings(self):
        from miyabi.settings import DEFAULT_SETTINGS
        with self.connection() as conn:
            row = conn.execute("SELECT data_json,updated_at FROM app_settings WHERE id=1").fetchone()
        return (json.loads(row[0]), row[1]) if row else (dict(DEFAULT_SETTINGS), None)

    def save_settings(self, values, expected_version):
        from miyabi.settings import validate_settings
        values = validate_settings(values)
        stamp = now()
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT updated_at FROM app_settings WHERE id=1").fetchone()
            if (row[0] if row else None) != expected_version:
                raise ConflictError("設定が他の画面で変更されました。設定を読み込み直してください。")
            conn.execute("INSERT OR REPLACE INTO app_settings VALUES (1,?,?)", (json.dumps(values, ensure_ascii=False), stamp))
        return stamp

    def publication(self, article_id):
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM publication_packs WHERE article_id=?", (article_id,)).fetchone()
        return None if row is None else {"article_id": row["article_id"], "data": json.loads(row["data_json"]),
                                         "source_updated_at": row["source_updated_at"], "updated_at": row["updated_at"]}

    def save_publication(self, article_id, values, source_version, expected_version):
        from miyabi.publication import validate_pack
        values = validate_pack(values)
        stamp = now()
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            article = conn.execute("SELECT updated_at FROM articles WHERE id=?", (article_id,)).fetchone()
            current = conn.execute("SELECT updated_at FROM publication_packs WHERE article_id=?", (article_id,)).fetchone()
            if article is None or article[0] != source_version:
                raise ConflictError("記事が変更または削除されました。投稿準備を退避し、記事の最新内容を読み込み直してください。")
            if (current[0] if current else None) != expected_version:
                raise ConflictError("投稿準備が他の画面で変更されました。退避して画面を再読み込みしてください。")
            conn.execute("INSERT OR REPLACE INTO publication_packs VALUES (?,?,?,?)",
                         (article_id, json.dumps(values, ensure_ascii=False), source_version, stamp))
        return stamp

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def get(self, article_id: int) -> dict | None:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
        return dict(row) if row else None

    def save(self, article: dict, article_id: int | None = None,
             expected_updated_at: str | None = None) -> int:
        values = empty_article() | {k: str(v) for k, v in article.items() if k in FIELDS}
        values["title"] = values["title"].strip()
        if not values["title"]:
            raise ValueError("タイトルを入力してください。仮のタイトルでも保存できます。")
        if values["status"] not in STATUSES:
            raise ValueError("記事ステータスが正しくありません。")
        if values["published_on"]:
            from datetime import date
            try:
                date.fromisoformat(values["published_on"])
            except ValueError as exc:
                raise ValueError("公開日は YYYY-MM-DD 形式で入力してください。") from exc
        if values["note_url"]:
            from urllib.parse import urlparse
            parsed = urlparse(values["note_url"])
            if parsed.scheme != "https" or parsed.hostname != "note.com":
                raise ValueError("note記事URLは https://note.com/ で始まるURLを入力してください。")
        stamp = now()
        with self.connection() as conn:
            if article_id is None:
                placeholders = ",".join("?" for _ in FIELDS)
                cur = conn.execute(
                    f"INSERT INTO articles (created_at,updated_at,{','.join(FIELDS)}) "
                    f"VALUES (?,?,{placeholders})", (stamp, stamp, *(values[k] for k in FIELDS)),
                )
                return int(cur.lastrowid)
            query = f"UPDATE articles SET updated_at=?,{','.join(k+'=?' for k in FIELDS)} WHERE id=?"
            args = [stamp, *(values[k] for k in FIELDS), article_id]
            if expected_updated_at is not None:
                query += " AND updated_at=?"
                args.append(expected_updated_at)
            cur = conn.execute(query, args)
            if cur.rowcount != 1:
                raise ConflictError("記事が他の画面で変更または削除されました。入力内容をダウンロードしてから記事を開き直してください。")
        return article_id

    def list(self, search: str = "", status: str = "すべて", order: str = "更新が新しい順") -> list[dict]:
        clauses, args = [], []
        if search.strip():
            # Treat SQL wildcard characters as literal search text.
            term = search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            clauses.append("(title LIKE ? ESCAPE '\\' OR body LIKE ? ESCAPE '\\' OR keyword LIKE ? ESCAPE '\\')")
            args.extend([f"%{term}%"] * 3)
        if status != "すべて":
            clauses.append("status=?")
            args.append(status)
        sorts = {"更新が新しい順": "updated_at DESC, id DESC", "作成が新しい順": "created_at DESC, id DESC",
                 "作成が古い順": "created_at ASC, id ASC", "タイトル順": "title ASC, id ASC"}
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM articles" + where + " ORDER BY " + sorts.get(order, sorts["更新が新しい順"]), args).fetchall()
        return [dict(row) for row in rows]

    def delete(self, article_id: int, expected_updated_at: str) -> None:
        with self.connection() as conn:
            cur = conn.execute("DELETE FROM articles WHERE id=? AND updated_at=?", (article_id, expected_updated_at))
            if cur.rowcount != 1:
                raise ConflictError("記事が変更または削除されました。一覧を更新して確認してください。")

    def duplicate(self, article_id: int) -> int:
        article = self.get(article_id)
        if article is None:
            raise ValueError("記事が見つかりません。")
        article.update(title=article["title"] + "（コピー）", status="アイデア", published_on="", note_url="")
        return self.save(article)
