"""Offline dashboard totals and transparent, deterministic theme suggestions."""
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo
from miyabi.database import GENRES, STATUSES

THEMES = {
    "暮らしを整える": ("暮らしを整える、小さな一歩の見つけ方", "片付けを始めるきっかけがほしい"),
    "人生の見直し": ("これから大切にしたい時間を見つめ直す", "自分の優先順位がわからない"),
    "新しい挑戦": ("初めての挑戦を無理なく続ける工夫", "やってみたいけれど不安がある"),
    "人間関係・家族": ("家族との会話で自分の気持ちも大切にする", "気をつかいすぎて疲れてしまう"),
    "健康と美容": ("無理なく続ける、自分をいたわる習慣", "自分の体をいたわる時間を持ちたい"),
    "お金とこれからの生活": ("これからの生活費を落ち着いて見直す第一歩", "家計のどこから見直せばよいかわからない"),
    "自分らしい生き方": ("周りと比べず、自分の好きなことを見つける", "自分の気持ちを後回しにしてしまう"),
    "数秘術を通じた自己理解": ("数秘術をきっかけに、自分の強みを振り返る", "自分の特徴を別の角度から考えたい"),
}


def summarize(articles, current=None):
    current = current or datetime.now(ZoneInfo("Asia/Tokyo"))
    month = current.astimezone(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m")
    statuses = Counter(a["status"] for a in articles)
    monthly = sum(datetime.fromisoformat(a["created_at"]).astimezone(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m") == month for a in articles)
    return {"total": len(articles), "in_progress": sum(statuses[s] for s in STATUSES[:4]),
            "complete": statuses["完成"], "published": statuses["公開済み"], "monthly": monthly,
            "statuses": {s: statuses[s] for s in STATUSES},
            "progress": sum(STATUSES.index(a["status"]) / (len(STATUSES) - 1) for a in articles) / len(articles) if articles else 0.0}


def recommend(articles):
    counts = Counter(a["genre"] for a in articles)
    titles = {a["title"].strip() for a in articles}
    candidates = []
    for genre in sorted(GENRES, key=lambda g: (counts[g], GENRES.index(g))):
        title, problem = THEMES[genre]
        if title in titles:
            continue
        candidates.append({"title": title, "genre": genre, "problem": problem,
                           "reason": f"保存済み記事が{counts[genre]}件のジャンルから提案しています。",
                           "paid_direction": "まず無料記事で考え方を紹介し、将来は書き込み式の実践シートなどへ発展できます。"})
    return candidates[:3]
