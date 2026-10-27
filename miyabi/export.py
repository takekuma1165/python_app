"""Exports contain the title, body and hashtags; private notes stay private."""
import re


def article_markdown(article: dict) -> str:
    title = article.get("title", "").strip() or "無題の記事"
    body = article.get("body", "").strip()
    tags = article.get("hashtags", "").strip()
    return f"# {title}\n\n{body}\n" + (f"\n{tags}\n" if tags else "")


def article_text(article: dict) -> str:
    text = article_markdown(article)
    text = re.sub(r"(?m)^#{1,6}\s+", "", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1（\2）", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    return text


def download_name(title: str, extension: str) -> str:
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip(" .")[:80] or "article"
    # Prefix avoids Windows reserved filenames (CON, AUX, COM1, etc.).
    return f"miyabi_{safe}.{extension}"
