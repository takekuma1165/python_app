"""Publication assets stay separate from the author's saved article."""
import re

PACK_FIELDS = ("title", "body", "hashtags", "introduction", "thread_1", "thread_2", "thread_3", "cover", "closing")


def split_tags(text):
    return list(dict.fromkeys("#" + tag.lstrip("#＃") for tag in re.split(r"[\s,、]+", text.strip()) if tag.lstrip("#＃")))


def empty_pack(article):
    return dict.fromkeys(PACK_FIELDS, "") | {key: article[key] for key in ("title", "body", "hashtags")}


def validate_pack(values):
    if not isinstance(values, dict) or set(values) != set(PACK_FIELDS) or any(not isinstance(v, str) for v in values.values()):
        raise ValueError("投稿準備データの項目が正しくありません。")
    if not values["title"].strip():
        raise ValueError("最終タイトルを入力してください。")
    if any(len(v) > 1000000 for v in values.values()):
        raise ValueError("投稿準備の文章が長すぎます。")
    if len(split_tags(values["hashtags"])) > 8:
        raise ValueError("ハッシュタグは8個以内にしてください。")
    if any(len(values[f"thread_{i}"]) > 500 for i in range(1, 4)):
        raise ValueError("Threads告知文は各500文字以内にしてください。")
    return dict(values)
