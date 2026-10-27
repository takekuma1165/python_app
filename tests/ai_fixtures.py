"""Clearly synthetic responses for deterministic offline tests."""
THEMES = {"themes": [dict(theme=f"暮らしの小さな一歩 {i}", audience="50代の女性", search_intent="無理なく暮らしを整えたい",
                          problem="片付けを始められない", benefit="小さな実践方法がわかる", keywords=["暮らし", "片付け"],
                          direction="無理のない実践", free_paid_fit="無料記事で共感、将来は実践ノートへ") for i in range(5)]}
TITLES = {"titles": [dict(title=f"暮らしを整える小さな一歩 {i}", search_intent="暮らしの整え方", appeal="身近な実践", improvement="経験で具体化する") for i in range(5)]}
OUTLINE = {"outline": "# 暮らしを整える\n\n導入：悩みへの共感（200字）\n\n## 小さな一歩（600字）\n### 引き出しから\n要点：一箇所から始める\n\n## まとめ（200字）",
           "checks": [dict(item=item, assessment="参考評価：確認しました") for item in ("検索意図", "見出し重複", "親子関係", "論理展開", "脱線", "順序")]}
BODY = {"body": "## 小さな一歩\n\n［ご自身の経験を入力してください］\n\nできることから始めませんか。", "experience_questions": ["実際に試したことを教えてください。"]}
RESULTS = {"themes": THEMES, "titles": TITLES, "outline": OUTLINE, "body": BODY}
