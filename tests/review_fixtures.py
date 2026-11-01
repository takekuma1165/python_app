"""Synthetic stage-three responses, not generated claims or real user material."""
SOURCE = "今日は公園に行きましした。家族と話す時間を大切にしています。今日は公園に行きましした。"
STYLE = {"converted": "今日は公園へ出かけました。家族と話す時間を、これからも大切にしたいですね。", "notes": ["意味と経験を保ちながらやさしい語尾にしました。"]}
ISSUES = [
    {"category": "誤字脱字", "before": "行きましした", "after": "行きました", "occurrence": 1, "reason": "誤字を修正します。", "requires_source": False},
    {"category": "誤字脱字", "before": "行きましした", "after": "行きました", "occurrence": 2, "reason": "二つ目の同じ誤字を修正します。", "requires_source": False},
    {"category": "同じ内容の重複", "before": "今日は公園に行きましした。", "after": "", "occurrence": 1, "reason": "同じ内容を削除する選択肢です。", "requires_source": False},
]
PROOF = {"issues": ISSUES}
DUPLICATE = {"findings": [{"article_id": "7", "current_quote": "家族と話す時間", "past_quote": "家族と話す時間", "reason": "同じ時間の過ごし方が題材です。", "suggestion": "別の具体的な場面を紹介することを検討します。"}]}
VALUES = {"title": "暮らしの時間", "genre": "暮らしを整える", "audience": "50代の女性", "body": SOURCE,
          "outline": "## 家族と話す時間", "style_mode": "やさしく温かい",
          "references": [{"article_id": "7", "title": "過去の記事", "excerpt": "家族と話す時間を大切に過ごしています。"}],
          "notes": "秘密の備考", "api_key": "秘密のキー", "unselected_article": "未選択の記事"}
