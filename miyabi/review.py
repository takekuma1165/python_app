"""Pure review operations: exact source patches and local Japanese similarity."""
from __future__ import annotations

import re
import unicodedata

STYLE_MODES = ("やさしく温かい", "親しみやすく自然", "共感を重視", "少し楽しく明るく", "落ち着いた大人の文章", "読者を引きつける導入文")
CHECK_CATEGORIES = ("誤字脱字", "不自然な日本語", "同じ言葉の繰り返し", "同じ内容の重複", "長すぎる文章",
                    "読みにくい表現", "見出しと本文の不一致", "断定的すぎる表現", "不安をあおる表現", "根拠が必要な記述")
MAX_LOCAL_CHARS = 100000
MAX_UNITS = 300


class ReviewError(ValueError):
    pass


def issue_span(source: str, issue: dict) -> tuple[int, int]:
    before = issue["before"]
    if not before:
        raise ReviewError("引用した原文が空欄のため自動適用できません。")
    start = -1
    for _ in range(issue["occurrence"]):
        start = source.find(before, start + 1)
        if start < 0:
            raise ReviewError("引用箇所が原文と一致しません。本文を確認して手動で修正してください。")
    return start, start + len(before)


def patched_body(source: str, issues: list[dict], accepted: list[int]) -> str:
    spans = []
    for index in accepted:
        if not 0 <= index < len(issues):
            raise ReviewError("修正候補を選び直してください。")
        item = issues[index]
        if item["requires_source"] or item["category"] == "根拠が必要な記述":
            raise ReviewError("根拠が必要な指摘は自動適用しません。出典と事実を確認して手動で修正してください。")
        start, end = issue_span(source, item)
        spans.append((start, end, item["after"]))
    spans.sort()
    cursor, parts = 0, []
    for start, end, after in spans:
        if start < cursor:
            raise ReviewError("すでに採用した修正と範囲が重なっています。校正をやり直すか、片方を元に戻してください。")
        parts.extend((source[cursor:start], after))
        cursor = end
    parts.append(source[cursor:])
    return "".join(parts)


def accept_issue(source: str, current: str, issues: list[dict], accepted: list[int], index: int):
    if index in accepted:
        raise ReviewError("この修正はすでに採用しています。")
    if current != patched_body(source, issues, accepted):
        raise ReviewError("校正後に本文が変わりました。現在の本文で再校正してください。")
    new_accepted = [*accepted, index]
    return patched_body(source, issues, new_accepted), new_accepted


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return "".join(c for c in text if c.isalnum())


def grams(text: str) -> set[str]:
    return {text[i:i + 3] for i in range(max(0, len(text) - 2))}


def units(body: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[。！？!?])|\n+", body)
            if len(normalize(part)) >= 12]


def overlap(a: set[str], b: set[str]) -> float:
    shared = len(a & b)
    return shared / min(len(a), len(b)) if min(len(a), len(b)) and shared >= 8 else 0.0


def local_duplicates(body: str, articles: list[dict], exclude_id=None, threshold: float = 0.65) -> dict:
    """Character 3-gram containment; a reference signal, not semantic proof."""
    if not body.strip():
        raise ReviewError("確認する本文を入力してください。")
    if len(body) > MAX_LOCAL_CHARS:
        raise ReviewError("ローカル確認は本文10万文字以内に分けて実行してください。")
    if not 0 <= threshold <= 1:
        raise ReviewError("類似度のしきい値を確認してください。")
    all_units = units(body)
    current_units = all_units[:MAX_UNITS]
    sets = [grams(normalize(u)) for u in current_units]
    internal = []
    for i, a in enumerate(sets):
        for j in range(i + 1, len(sets)):
            score = overlap(a, sets[j])
            if score >= threshold:
                internal.append({"first": i + 1, "second": j + 1, "before": current_units[i],
                                 "similar": current_units[j], "score": round(score, 3),
                                 "kind": "表記を整えると同一" if normalize(current_units[i]) == normalize(current_units[j]) else "表現が似ている"})
    body_grams = grams(normalize(body))
    matches, skipped, checked, limited_articles = [], [], 0, []
    for article in articles:
        if exclude_id is not None and str(article["id"]) == str(exclude_id):
            continue
        text = article.get("body", "")
        if not text.strip():
            continue
        if len(text) > MAX_LOCAL_CHARS:
            skipped.append(article["id"])
            continue
        checked += 1
        candidates = units(text)
        if len(candidates) > MAX_UNITS:
            limited_articles.append(article["id"])
        best, excerpt = 0.0, ""
        for part in candidates[:MAX_UNITS]:
            score = overlap(body_grams, grams(normalize(part)))
            if score > best:
                best, excerpt = score, part
        # Whole-body overlap catches a copy even with sentence boundaries changed.
        full_score = overlap(body_grams, grams(normalize(text)))
        if full_score > best:
            best, excerpt = full_score, text[:600]
        if best >= threshold:
            current_excerpt = max(current_units, key=lambda u: overlap(grams(normalize(u)), grams(normalize(excerpt))), default=body[:600])
            matches.append({"id": article["id"], "title": article["title"], "score": round(best, 3),
                            "excerpt": excerpt[:1000], "current_excerpt": current_excerpt[:1000]})
    internal.sort(key=lambda row: (-row["score"], row["first"], row["second"]))
    matches.sort(key=lambda row: (-row["score"], row["id"]))
    return {"internal": internal[:20], "past": matches[:20], "internal_total": len(internal), "past_total": len(matches),
            "checked_articles": checked, "units_total": len(all_units), "units_checked": len(current_units),
            "skipped_articles": skipped, "limited_articles": limited_articles, "threshold": threshold}
