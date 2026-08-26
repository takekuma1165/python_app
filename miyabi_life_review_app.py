from __future__ import annotations

import streamlit as st


# =========================================================
# 基本設定
# =========================================================
st.set_page_config(
    page_title="これからの人生 見直し診断｜みやび",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

APP_TITLE = "これからの人生 見直し診断"
APP_SUBTITLE = "今の暮らし、少し見直してみませんか？"

# note記事のURLが決まったら、"" の中に貼り付けてください。
# 例：
# "眠れない夜に見直したい5つの習慣": "https://note.com/xxxxx/n/xxxxx"
ARTICLE_URLS = {
    "眠れない夜に見直したい5つの習慣": "",
    "健康のために毎日続けたい小さなこと": "",
    "香りの効果を解説 睡眠を整える香り6選": "",
    "将来のお金が不安なときに最初に整理したい3つのこと": "",
    "40代から考えたい、これからのお金との付き合い方": "",
    "家族のためだけでなく、自分のためにも時間を使う": "",
    "香りの取り入れ方 自宅でできる簡単習慣5選": "",
    "一人で悩まないために大切にしたい人とのつながり": "",
    "家族との関係に疲れたとき、少し心を軽くする考え方": "",
    "これからやってみたいことを見つける小さなヒント": "",
    "何歳からでも遅くない、新しいことを始めるコツ": "",
}


# =========================================================
# デザイン
# =========================================================
st.markdown(
    """
    <style>
    :root {
        --miyabi-green: #5f8268;
        --miyabi-deep: #385845;
        --miyabi-light: #edf5ef;
        --miyabi-cream: #fbfaf5;
        --miyabi-gold: #b89a62;
        --miyabi-text: #2f3932;
        --miyabi-muted: #6d776f;
    }

    .stApp {
        background:
            radial-gradient(circle at 10% 10%, rgba(218, 236, 220, 0.65), transparent 26%),
            radial-gradient(circle at 90% 5%, rgba(239, 230, 205, 0.60), transparent 28%),
            linear-gradient(180deg, #fbfcf8 0%, #f7faf6 55%, #fbfaf5 100%);
        color: var(--miyabi-text);
    }

    .block-container {
        max-width: 860px;
        padding-top: 2.2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        color: var(--miyabi-deep);
        letter-spacing: 0.02em;
    }

    .hero {
        background: rgba(255, 255, 255, 0.86);
        border: 1px solid rgba(95, 130, 104, 0.16);
        border-radius: 28px;
        padding: 34px 32px 30px 32px;
        box-shadow: 0 14px 40px rgba(56, 88, 69, 0.08);
        text-align: center;
        margin-bottom: 22px;
    }

    .hero-badge {
        display: inline-block;
        padding: 7px 13px;
        border-radius: 999px;
        background: var(--miyabi-light);
        color: var(--miyabi-deep);
        font-size: 0.83rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        margin-bottom: 14px;
    }

    .hero-title {
        font-size: clamp(1.9rem, 5vw, 3rem);
        line-height: 1.25;
        font-weight: 800;
        color: var(--miyabi-deep);
        margin-bottom: 12px;
    }

    .hero-subtitle {
        color: var(--miyabi-muted);
        font-size: 1.08rem;
        line-height: 1.9;
        margin: 0 auto;
        max-width: 650px;
    }

    .mini-note {
        margin-top: 18px;
        font-size: 0.86rem;
        color: #7b837d;
    }

    .section-card {
        background: rgba(255,255,255,0.90);
        border: 1px solid rgba(95, 130, 104, 0.14);
        border-radius: 22px;
        padding: 22px 22px 8px 22px;
        box-shadow: 0 8px 28px rgba(56, 88, 69, 0.06);
        margin: 15px 0 22px 0;
    }

    .section-label {
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        color: var(--miyabi-gold);
        margin-bottom: 4px;
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: var(--miyabi-deep);
        margin-bottom: 5px;
    }

    .section-desc {
        font-size: 0.9rem;
        color: var(--miyabi-muted);
        margin-bottom: 12px;
    }

    div[data-testid="stRadio"] {
        background: rgba(250, 252, 248, 0.82);
        border: 1px solid rgba(95, 130, 104, 0.10);
        padding: 12px 14px 9px 14px;
        border-radius: 16px;
        margin-bottom: 8px;
    }

    div[data-testid="stRadio"] label p {
        color: var(--miyabi-text);
    }

    .stButton > button,
    div[data-testid="stFormSubmitButton"] > button {
        width: 100%;
        border: 0;
        border-radius: 999px;
        background: linear-gradient(135deg, #5f8268 0%, #42634e 100%);
        color: white;
        font-weight: 800;
        min-height: 48px;
        box-shadow: 0 8px 20px rgba(66, 99, 78, 0.18);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }

    .stButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        color: white;
        transform: translateY(-1px);
        box-shadow: 0 10px 24px rgba(66, 99, 78, 0.23);
    }

    .result-wrap {
        background: linear-gradient(145deg, rgba(255,255,255,0.96), rgba(239,247,241,0.96));
        border: 1px solid rgba(95, 130, 104, 0.20);
        border-radius: 28px;
        padding: 28px;
        box-shadow: 0 16px 40px rgba(56, 88, 69, 0.10);
        margin: 12px 0 22px 0;
    }

    .result-kicker {
        color: var(--miyabi-gold);
        font-size: 0.82rem;
        letter-spacing: 0.12em;
        font-weight: 800;
    }

    .result-title {
        font-size: clamp(1.6rem, 4.5vw, 2.35rem);
        line-height: 1.35;
        color: var(--miyabi-deep);
        font-weight: 900;
        margin: 8px 0 12px 0;
    }

    .result-text {
        color: var(--miyabi-text);
        font-size: 1rem;
        line-height: 1.95;
    }

    .miyabi-message {
        background: #fffdf8;
        border-left: 5px solid var(--miyabi-gold);
        border-radius: 14px;
        padding: 18px 18px 16px 18px;
        margin: 18px 0 12px 0;
        line-height: 1.9;
    }

    .bar-row {
        margin: 12px 0 15px 0;
    }

    .bar-head {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        font-size: 0.90rem;
        color: var(--miyabi-text);
        margin-bottom: 6px;
    }

    .bar-track {
        width: 100%;
        height: 10px;
        background: #e9eee9;
        border-radius: 999px;
        overflow: hidden;
    }

    .bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #87a88e 0%, #5f8268 100%);
        border-radius: 999px;
    }

    .article-card {
        background: white;
        border: 1px solid rgba(95, 130, 104, 0.15);
        border-radius: 18px;
        padding: 16px 17px;
        margin: 10px 0;
        box-shadow: 0 6px 18px rgba(56, 88, 69, 0.05);
    }

    .article-title {
        font-weight: 800;
        color: var(--miyabi-deep);
        line-height: 1.55;
    }

    .article-sub {
        font-size: 0.82rem;
        color: var(--miyabi-muted);
        margin-top: 5px;
    }

    .soft-caption {
        color: var(--miyabi-muted);
        font-size: 0.85rem;
        line-height: 1.7;
    }

    .footer {
        text-align: center;
        color: #7f8981;
        font-size: 0.80rem;
        line-height: 1.8;
        padding-top: 24px;
    }

    @media (max-width: 700px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 1.2rem;
        }
        .hero {
            padding: 26px 18px 24px 18px;
            border-radius: 22px;
        }
        .result-wrap {
            padding: 22px 18px;
            border-radius: 22px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 診断データ
# =========================================================
OPTIONS = [
    "あてはまらない",
    "あまりあてはまらない",
    "少しあてはまる",
    "とてもあてはまる",
]
SCORE_MAP = {
    "あてはまらない": 0,
    "あまりあてはまらない": 1,
    "少しあてはまる": 2,
    "とてもあてはまる": 3,
}

SECTIONS = [
    {
        "key": "health",
        "label": "HEALTH & SLEEP",
        "title": "健康・睡眠",
        "desc": "まずは、体と休息について振り返ります。",
        "questions": [
            "最近、朝すっきり起きられないことが多い。",
            "疲れが翌日まで残ると感じることがある。",
            "健康のために何か始めたいけれど、何から手をつけるか迷っている。",
        ],
    },
    {
        "key": "money",
        "label": "MONEY & FUTURE",
        "title": "お金・将来",
        "desc": "漠然とした不安を、今の気持ちとして確認します。",
        "questions": [
            "これからのお金について、漠然とした不安がある。",
            "今後の生活に必要なお金を、まだ十分にイメージできていない。",
            "お金のことを考えたいと思いながら、つい後回しにしている。",
        ],
    },
    {
        "key": "self_time",
        "label": "MY TIME",
        "title": "自分の時間",
        "desc": "家族や仕事だけでなく、自分自身の時間にも目を向けます。",
        "questions": [
            "自分だけの時間が足りないと感じる。",
            "家族や仕事を優先して、自分のことを後回しにすることが多い。",
            "最近、心から楽しいと思える時間が少ない。",
        ],
    },
    {
        "key": "relationships",
        "label": "RELATIONSHIPS",
        "title": "人とのつながり",
        "desc": "家族・友人・周囲との距離感を振り返ります。",
        "questions": [
            "家族との関係で、少し気になっていることがある。",
            "気軽に話せる人が、もう少しいたらいいなと思う。",
            "悩みを一人で抱え込んでしまうことがある。",
        ],
    },
    {
        "key": "future",
        "label": "NEXT STEP",
        "title": "これから・新しい一歩",
        "desc": "未来への気持ちや、新しいことへの準備度を見ていきます。",
        "questions": [
            "これからやってみたいことがある。",
            "新しいことを学んだり、始めたりしてみたい。",
            "これからの人生に、楽しみにしていることがある。",
        ],
    },
]

RESULTS = {
    "health": {
        "emoji": "🌿",
        "title": "健康を少し大切にしたい時期",
        "lead": "今は、頑張ることを増やすより、体と心の土台を整えることが大切な時期かもしれません。",
        "body": (
            "睡眠、疲れ、食事、軽い運動など、毎日の小さな習慣を一度に全部変える必要はありません。"
            "まずは「今日は少し早く休む」「10分だけ歩く」など、続けやすいことを一つ選んでみましょう。"
        ),
        "action": "今夜、いつもより15分早く休む準備をする。",
        "articles": [
            "眠れない夜に見直したい5つの習慣",
            "健康のために毎日続けたい小さなこと",
            "香りの効果を解説 睡眠を整える香り6選",
        ],
    },
    "money": {
        "emoji": "🕊️",
        "title": "将来のお金を整理したい時期",
        "lead": "不安の正体がまだぼんやりしているなら、まず「見える化」することから始めると心が軽くなります。",
        "body": (
            "収入・支出・貯蓄・今後かかりそうなお金を、正確でなくてもよいので書き出してみましょう。"
            "数字にすることで、「何となく不安」から「今できること」へ考えを移しやすくなります。"
        ),
        "action": "今月の固定費を3つだけ書き出す。",
        "articles": [
            "将来のお金が不安なときに最初に整理したい3つのこと",
            "40代から考えたい、これからのお金との付き合い方",
        ],
    },
    "self_time": {
        "emoji": "☕",
        "title": "自分の時間を取り戻したい時期",
        "lead": "家族や仕事を大切にしてきた分、自分自身のことが後回しになっているのかもしれません。",
        "body": (
            "これからは「何をしなければならないか」だけでなく、「私は何をすると心地よいか」も大切にしてみましょう。"
            "短い時間でも、自分のために使う時間は暮らしの余白になります。"
        ),
        "action": "今週、自分のためだけの30分を予定に入れる。",
        "articles": [
            "家族のためだけでなく、自分のためにも時間を使う",
            "香りの取り入れ方 自宅でできる簡単習慣5選",
        ],
    },
    "relationships": {
        "emoji": "🤝",
        "title": "人とのつながりを見直したい時期",
        "lead": "人間関係は、数よりも「安心して話せるか」「自分らしくいられるか」が大切です。",
        "body": (
            "無理に誰かに合わせる必要はありません。少し距離を取ったほうが楽な関係もあれば、"
            "今までより少し連絡を増やしたい相手もいるかもしれません。自分が心地よい距離を探してみましょう。"
        ),
        "action": "話したい人を一人思い浮かべて、短い連絡をしてみる。",
        "articles": [
            "一人で悩まないために大切にしたい人とのつながり",
            "家族との関係に疲れたとき、少し心を軽くする考え方",
        ],
    },
    "future": {
        "emoji": "✨",
        "title": "新しいことを始める準備ができている時期",
        "lead": "今のあなたには、「これから」に目を向ける力が少しずつ育っているようです。",
        "body": (
            "大きな目標でなくても大丈夫です。気になっていることを調べる、体験してみる、"
            "一人で始めてみる。そんな小さな一歩が、これからの楽しみにつながっていきます。"
        ),
        "action": "やってみたいことを3つ、紙やスマホに書き出す。",
        "articles": [
            "これからやってみたいことを見つける小さなヒント",
            "何歳からでも遅くない、新しいことを始めるコツ",
        ],
    },
}

TYPE_LABELS = {
    "health": "健康・睡眠",
    "money": "お金・将来",
    "self_time": "自分の時間",
    "relationships": "人とのつながり",
    "future": "これから",
}


# =========================================================
# 関数
# =========================================================
def init_state() -> None:
    if "page" not in st.session_state:
        st.session_state.page = "intro"
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "result_key" not in st.session_state:
        st.session_state.result_key = None
    if "scores" not in st.session_state:
        st.session_state.scores = {}


def reset_app() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def determine_result(scores: dict[str, int]) -> tuple[str, list[str]]:
    """
    4分野は「見直しサイン」、futureだけは「新しい一歩の準備度」。
    未来への準備度が高く、他分野が極端に高くない場合は future を優先します。
    それ以外は、見直しサインが最も高い分野を結果タイプにします。
    """
    attention_keys = ["health", "money", "self_time", "relationships"]
    max_attention = max(scores[k] for k in attention_keys)
    future_score = scores["future"]

    # 新しいことへの前向きさが強く、生活のどこかに非常に強い負担サインが出ていない場合
    if future_score >= 7 and max_attention <= 7:
        primary = "future"
    else:
        priority_order = ["health", "self_time", "relationships", "money"]
        primary = max(priority_order, key=lambda k: (scores[k], -priority_order.index(k)))

    # 次に強いヒントを1〜2個残す
    ranked = sorted(
        scores.keys(),
        key=lambda k: scores[k],
        reverse=True,
    )
    secondary = [k for k in ranked if k != primary][:2]
    return primary, secondary


def render_bar(label: str, value: int, caption: str) -> None:
    percent = int(round(value / 9 * 100))
    st.markdown(
        f"""
        <div class="bar-row">
            <div class="bar-head">
                <span><strong>{label}</strong> <span style="color:#7b837d;">{caption}</span></span>
                <span>{percent}%</span>
            </div>
            <div class="bar-track">
                <div class="bar-fill" style="width:{percent}%"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_article(title: str) -> None:
    url = ARTICLE_URLS.get(title, "")
    if url:
        st.markdown(
            f"""
            <div class="article-card">
                <div class="article-title">📖 {title}</div>
                <div class="article-sub">診断結果に合わせて選んだ、みやびのおすすめ記事です。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.link_button("この記事を読む", url, use_container_width=True)
    else:
        st.markdown(
            f"""
            <div class="article-card">
                <div class="article-title">📖 {title}</div>
                <div class="article-sub">note公開後、このカードから記事へつなげられます。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# 画面
# =========================================================
init_state()

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-badge">MIYABI LIFE CHECK</div>
        <div class="hero-title">{APP_TITLE}</div>
        <div class="hero-subtitle">
            {APP_SUBTITLE}<br>
            健康・お金・自分の時間・人とのつながり・これからのこと。<br>
            15の質問から、今のあなたが少し大切にしたいことを見つけます。
        </div>
        <div class="mini-note">所要時間：約3分　｜　正解・不正解はありません</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.page == "intro":
    st.markdown("### 🌱 この診断でわかること")
    st.write(
        "今の暮らしを5つの方向からやさしく振り返り、"
        "「これから何を少し大切にするとよいか」を1つのタイプとしてお伝えします。"
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("質問", "15問")
    c2.metric("診断タイプ", "5種類")
    c3.metric("時間", "約3分")

    st.info(
        "この診断は医療・心理・金融などの専門的な判定を行うものではありません。"
        "暮らしを振り返るためのセルフチェックとしてご利用ください。",
        icon="💡",
    )

    if st.button("診断をはじめる", type="primary"):
        st.session_state.page = "quiz"
        st.rerun()


elif st.session_state.page == "quiz":
    st.markdown("### 直感で、今の自分に近いものを選んでください")
    st.caption("深く考えすぎず、「今はこうかも」と感じる答えで大丈夫です。")

    with st.form("life_review_form", clear_on_submit=False):
        q_number = 1
        answers = {}

        for section in SECTIONS:
            st.markdown(
                f"""
                <div class="section-card">
                    <div class="section-label">{section["label"]}</div>
                    <div class="section-title">{section["title"]}</div>
                    <div class="section-desc">{section["desc"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            for question in section["questions"]:
                key = f"q{q_number}"
                answers[key] = st.radio(
                    f"Q{q_number}. {question}",
                    OPTIONS,
                    index=None,
                    horizontal=False,
                    key=key,
                )
                q_number += 1

        submitted = st.form_submit_button("診断結果を見る", type="primary", use_container_width=True)

        if submitted:
            unanswered = [k for k, v in answers.items() if v is None]
            if unanswered:
                st.error(f"未回答の質問が {len(unanswered)} 問あります。すべて回答してから結果をご覧ください。")
            else:
                scores = {}
                q_index = 1
                for section in SECTIONS:
                    section_score = 0
                    for _ in section["questions"]:
                        section_score += SCORE_MAP[answers[f"q{q_index}"]]
                        q_index += 1
                    scores[section["key"]] = section_score

                result_key, secondary = determine_result(scores)

                st.session_state.answers = answers
                st.session_state.scores = scores
                st.session_state.result_key = result_key
                st.session_state.secondary = secondary
                st.session_state.page = "result"
                st.rerun()


elif st.session_state.page == "result":
    result_key = st.session_state.result_key
    result = RESULTS[result_key]
    scores = st.session_state.scores
    secondary = st.session_state.get("secondary", [])

    st.markdown(
        f"""
        <div class="result-wrap">
            <div class="result-kicker">YOUR RESULT</div>
            <div class="result-title">{result["emoji"]} {result["title"]}</div>
            <div class="result-text">
                <strong>{result["lead"]}</strong><br><br>
                {result["body"]}
            </div>
            <div class="miyabi-message">
                <strong>みやびから、あなたへ</strong><br>
                これからの人生を全部変える必要はありません。<br>
                今日できる小さなことを一つ見つけるだけでも十分です。<br>
                一緒に、これからの暮らしを少しずつ楽しくしていきませんか。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🍀 今日の小さな一歩")
    st.success(result["action"])

    st.markdown("### あなたの5つのバランス")
    st.markdown(
        '<div class="soft-caption">4分野は「見直しサイン」、最後の1分野は「新しい一歩の準備度」です。高いほど、そのテーマが今のあなたに強く表れています。</div>',
        unsafe_allow_html=True,
    )
    render_bar("健康・睡眠", scores["health"], "見直しサイン")
    render_bar("お金・将来", scores["money"], "見直しサイン")
    render_bar("自分の時間", scores["self_time"], "見直しサイン")
    render_bar("人とのつながり", scores["relationships"], "見直しサイン")
    render_bar("これから", scores["future"], "一歩の準備度")

    if secondary:
        labels = "、".join(TYPE_LABELS[k] for k in secondary)
        st.caption(f"もう一つのヒント：{labels}にも、今の気持ちが少し表れています。")

    st.markdown("### 📚 あなたにおすすめの記事")
    st.write("診断結果に近いテーマから、読みやすい記事を選びました。")
    for article in result["articles"]:
        render_article(article)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("もう一度診断する"):
            reset_app()
    with col2:
        if st.button("最初の画面に戻る"):
            st.session_state.page = "intro"
            st.rerun()

st.markdown(
    """
    <div class="footer">
        みやび｜これからの毎日を、少しずつ楽しく。<br>
        この診断は暮らしを振り返るためのセルフチェックです。
    </div>
    """,
    unsafe_allow_html=True,
)
