"""Non-secret defaults and a small local pointer to the chosen data folder."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

DEFAULT_SETTINGS = {
    "model": "gpt-4.1-mini", "ai_enabled": False, "tone": "温かく親しみやすい、やさしいです・ます調",
    "audience": "40代・50代・60代以上の女性", "word_count": 2000,
}


def validate_settings(values):
    if not isinstance(values, dict) or set(values) != set(DEFAULT_SETTINGS):
        raise ValueError("設定の項目が正しくありません。")
    for key, limit in (("model", 120), ("tone", 500), ("audience", 500)):
        if not isinstance(values[key], str) or not values[key].strip() or len(values[key]) > limit:
            raise ValueError("モデル・文章トーン・想定読者は空欄にせず、長すぎない内容で指定してください。")
    if any(c.isspace() for c in values["model"]):
        raise ValueError("モデル名に空白は使えません。")
    if type(values["ai_enabled"]) is not bool or type(values["word_count"]) is not int or not 200 <= values["word_count"] <= 6000:
        raise ValueError("AI利用設定、または標準文字数（200〜6000）を確認してください。")
    return dict(values)


def config_path(root):
    return Path(os.environ.get("MIYABI_CONFIG_PATH") or Path(root) / "local_config.json").expanduser()


def resolve_data_dir(root):
    value = os.environ.get("MIYABI_DATA_DIR", "").strip()
    path = config_path(root)
    if not value and path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or set(data) != {"data_dir"} or not isinstance(data["data_dir"], str):
            raise ValueError("保存先設定ファイルが正しくありません。")
        value = data["data_dir"].strip()
    folder = Path(value or "data").expanduser()
    return folder if folder.is_absolute() else Path(root) / folder


def move_data_folder(store, root, destination):
    """Copy a consistent SQLite snapshot; switch the pointer only after success."""
    if os.environ.get("MIYABI_DATA_DIR", "").strip():
        raise ValueError("MIYABI_DATA_DIR が環境変数または .env で指定されています。そちらを編集して再起動してください。")
    if not destination.strip():
        raise ValueError("新しい保存先フォルダーを入力してください。")
    folder = Path(destination).expanduser()
    if not folder.is_absolute():
        folder = Path(root) / folder
    folder = folder.resolve()
    if folder == store.path.parent.resolve():
        raise ValueError("現在と異なる保存先を指定してください。")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "miyabi.sqlite3"
    # Exclusive creation refuses to overwrite an existing user's database.
    with target.open("xb"):
        pass
    try:
        import sqlite3
        with store.connection() as source:
            dest = sqlite3.connect(target)
            try:
                source.backup(dest)
                if dest.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("コピーしたデータベースを検証できませんでした。")
            finally:
                dest.close()
    except Exception:
        target.unlink(missing_ok=True)  # Only our exclusively created file.
        raise
    pointer = config_path(root)
    pointer.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=pointer.parent, prefix=".miyabi-config-", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump({"data_dir": str(folder)}, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, pointer)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return target
