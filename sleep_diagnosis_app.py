import streamlit as st

# ---------------------------------
# 基本設定
# ---------------------------------
st.set_page_config(
    page_title="睡眠セルフチェック",
    page_icon="🌙",
    layout="centered",
)

st.title("🌙 睡眠セルフチェック")
st.write(
    "過去2週間の睡眠を振り返り、最も近いものを選んでください。"
)
st.info(
    "このチェックは、生活習慣を振り返るためのものです。"
    "病気の診断や治療を目的としたものではありません。"
)

# ---------------------------------
# 回答選択肢
# ---------------------------------
score_options = {
    "まったくない": 0,
    "週に1日未満": 1,
    "週に1～2日": 2,
    "週に3～4日": 3,
    "ほぼ毎日": 4,
}

yes_no_options = ["いいえ", "はい"]

# ---------------------------------
# 設問データ
# category は睡眠タイプ判定に使用
# ---------------------------------
questions = [
    {
        "id": 1,
        "category": "生活リズム",
        "text": "必要だと感じる時間より、睡眠時間が短くなっていますか？",
    },
    {
        "id": 2,
        "category": "生活リズム",
        "text": "寝る時間や起きる時間が、日によって大きく変わりますか？",
    },
    {
        "id": 3,
        "category": "生活リズム",
        "text": "夕方以降に、30分以上うたた寝をすることがありますか？",
    },
    {
        "id": 4,
        "category": "寝つき",
        "text": "布団に入ってから眠るまで、30分以上かかりますか？",
    },
    {
        "id": 5,
        "category": "途中覚醒",
        "text": "夜中に何度も目が覚めますか？",
    },
    {
        "id": 6,
        "category": "途中覚醒",
        "text": "予定していた時間より早く目が覚め、その後眠れないことがありますか？",
    },
    {
        "id": 7,
        "category": "休養感",
        "text": "朝起きたとき、『よく眠れた』という満足感がありませんか？",
    },
    {
        "id": 8,
        "category": "休養感",
        "text": "十分寝たつもりでも、疲れが残っていますか？",
    },
    {
        "id": 9,
        "category": "休養感",
        "text": "日中、仕事や家事に支障が出るほど眠くなることがありますか？",
    },
    {
        "id": 10,
        "category": "休養感",
        "text": "睡眠不足によって、集中力や意欲が低下していると感じますか？",
    },
    {
        "id": 11,
        "category": "寝つき",
        "text": "寝る直前まで、スマートフォンやパソコンを見ていますか？",
    },
    {
        "id": 12,
        "category": "寝つき",
        "text": "夕方以降に、コーヒー・緑茶・エナジードリンクなどを飲みますか？",
    },
    {
        "id": 13,
        "category": "途中覚醒",
        "text": "眠るために、お酒を飲むことがありますか？",
    },
    {
        "id": 14,
        "category": "生活リズム",
        "text": "寝る直前に食事や夜食を取ることがありますか？",
    },
    {
        "id": 15,
        "category": "途中覚醒",
        "text": "寝室の明るさ、音、暑さ、寒さが気になりますか？",
    },
    {
        "id": 16,
        "category": "心配事",
        "text": "心配事や考え事が頭から離れず、眠れないことがありますか？",
    },
    {
        "id": 17,
        "category": "途中覚醒",
        "text": "夜中にトイレへ行くため、何度も目が覚めますか？",
    },
    {
        "id": 18,
        "category": "途中覚醒",
        "text": "身体の痛みやかゆみなどで、睡眠が妨げられますか？",
    },
]

warning_questions = [
    {
        "id": 19,
        "text": "大きないびきを指摘されたことがありますか？",
    },
    {
        "id": 20,
        "text": "寝ている間に呼吸が止まっていると言われたことがありますか？",
    },
    {
        "id": 21,
        "text": "眠っている時間は確保できているのに、日中に強い眠気がありますか？",
    },
    {
        "id": 22,
        "text": "運転中や仕事中に、眠りそうになったことがありますか？",
    },
    {
        "id": 23,
        "text": "足がむずむずして、動かさないと落ち着かず眠れないことがありますか？",
    },
    {
        "id": 24,
        "text": "睡眠の悩みが週3日以上あり、長く続いていますか？",
    },
]

# ---------------------------------
# 診断ロジック
# ---------------------------------
def get_severity(total_score: int) -> tuple[str, str]:
    """合計点から睡眠状態を判定する。"""
    if total_score <= 14:
        return (
            "おおむね安定タイプ",
            "現在の睡眠状態は比較的安定しているようです。"
            "今の生活リズムを大切にしながら、疲れを感じる日は少し早めに休みましょう。",
        )
    if total_score <= 28:
        return (
            "小さな乱れタイプ",
            "寝る前の習慣や生活リズムに、睡眠を妨げる原因がありそうです。"
            "まずは起きる時間を整え、夕方以降のカフェインや"
            "寝る前のスマートフォンを見直してみましょう。",
        )
    if total_score <= 43:
        return (
            "睡眠を見直したいタイプ",
            "寝つき、途中覚醒、睡眠不足など、複数の悩みが重なっている可能性があります。"
            "一度にすべて変えず、最も点数が高かった項目から一つずつ整えてみましょう。",
        )
    return (
        "専門家への相談も考えたいタイプ",
        "睡眠の悩みが日中の生活にも影響している可能性があります。"
        "生活習慣を整えても改善しない場合や、症状が長く続いている場合は、"
        "かかりつけ医や睡眠を扱う医療機関への相談も検討しましょう。",
    )


def get_sleep_type(category_scores: dict[str, int]) -> tuple[str, str]:
    """カテゴリ別得点から主な睡眠タイプを判定する。"""
    max_score = max(category_scores.values())
    top_categories = [
        category
        for category, score in category_scores.items()
        if score == max_score
    ]

    # 同点の場合は、より具体的なタイプを優先
    priority = ["休養感", "途中覚醒", "寝つき", "心配事", "生活リズム"]
    top_category = next(
        category for category in priority if category in top_categories
    )

    type_messages = {
        "寝つき": (
            "寝つきに時間がかかるタイプ",
            "頭や身体が、まだ活動モードのままかもしれません。"
            "寝る前は照明を少し落とし、スマートフォンを置いて、"
            "ゆっくり過ごす時間を作ってみましょう。",
        ),
        "途中覚醒": (
            "夜中に目が覚めるタイプ",
            "寝室環境、寝酒、夜間のトイレ、身体の不調などが、"
            "睡眠を途切れさせている可能性があります。"
            "思い当たる原因を一つずつ確認してみましょう。",
        ),
        "生活リズム": (
            "睡眠不足・リズム乱れタイプ",
            "睡眠時間と生活リズムの乱れが影響しているようです。"
            "まずは毎朝の起床時間を、できる範囲でそろえてみましょう。",
        ),
        "休養感": (
            "眠っても疲れが取れないタイプ",
            "睡眠時間だけでなく、睡眠の質が低下している可能性があります。"
            "日中の強い眠気が続く場合は、専門家への相談も大切です。",
        ),
        "心配事": (
            "心配事で眠れないタイプ",
            "考え事を無理に止めようとせず、紙に書き出したり、"
            "呼吸をゆっくり整えたりして、頭を休ませる時間を作ってみましょう。",
        ),
    }
    return type_messages[top_category]


def get_aroma_message(aroma_preference: str, method: str) -> str:
    """香りの好みと使用方法から提案文を作る。"""
    aroma_messages = {
        "花のような香り": (
            "ラベンダーなど、やさしい花の香りが向いているかもしれません。"
        ),
        "森や木の香り": (
            "ヒノキやシダーウッドなど、落ち着いた木の香りが向いているかもしれません。"
        ),
        "柑橘系の香り": (
            "ベルガモットなど、穏やかな柑橘系の香りが向いているかもしれません。"
        ),
        "石けんのような香り": (
            "清潔感のある、やさしく控えめな香りから試してみましょう。"
        ),
        "香りは使いたくない": (
            "香りを無理に使う必要はありません。深呼吸、ストレッチ、"
            "照明を暗くするなど、別の方法を選びましょう。"
        ),
    }

    if aroma_preference == "香りは使いたくない":
        return aroma_messages[aroma_preference]

    return (
        f"{aroma_messages[aroma_preference]}"
        f"取り入れ方は『{method}』から、少量で試してみてください。"
        "香りが強すぎると不快感や頭痛につながることがあるため、"
        "心地よいと感じる範囲にとどめましょう。"
    )


# ---------------------------------
# 入力フォーム
# ---------------------------------
with st.form("sleep_check_form"):
    st.subheader("1．睡眠状態について")
    st.caption("すべての項目に回答してください。")

    answers = {}

    for question in questions:
        answers[question["id"]] = st.radio(
            f"Q{question['id']}．{question['text']}",
            options=list(score_options.keys()),
            horizontal=False,
            key=f"q_{question['id']}",
        )

    st.divider()
    st.subheader("2．注意して確認したい項目")
    st.caption("以下の項目は合計点には含まれません。")

    warning_answers = {}

    for question in warning_questions:
        warning_answers[question["id"]] = st.radio(
            f"Q{question['id']}．{question['text']}",
            options=yes_no_options,
            horizontal=True,
            key=f"warning_{question['id']}",
        )

    st.divider()
    st.subheader("3．香りについて")

    aroma_interest = st.radio(
        "Q25．眠る前に香りを取り入れてみたいですか？",
        options=[
            "ぜひ取り入れたい",
            "少し興味がある",
            "香りが苦手",
            "分からない",
        ],
        key="aroma_interest",
    )

    aroma_preference = st.radio(
        "Q26．心地よいと感じる香りはどれですか？",
        options=[
            "花のような香り",
            "森や木の香り",
            "柑橘系の香り",
            "石けんのような香り",
            "香りは使いたくない",
        ],
        key="aroma_preference",
    )

    aroma_method = st.radio(
        "Q27．寝る前に続けやすい方法はどれですか？",
        options=[
            "ティッシュやコットンに香りをつける",
            "アロマストーンを使う",
            "入浴時に香りを楽しむ",
            "香りのミストを使う",
            "香り以外の方法を選ぶ",
        ],
        key="aroma_method",
    )

    submitted = st.form_submit_button(
        "診断結果を見る",
        type="primary",
        use_container_width=True,
    )

# ---------------------------------
# 結果表示
# ---------------------------------
if submitted:
    total_score = sum(score_options[answer] for answer in answers.values())

    category_scores = {
        "生活リズム": 0,
        "寝つき": 0,
        "途中覚醒": 0,
        "休養感": 0,
        "心配事": 0,
    }

    for question in questions:
        category = question["category"]
        category_scores[category] += score_options[answers[question["id"]]]

    severity_title, severity_message = get_severity(total_score)
    sleep_type_title, sleep_type_message = get_sleep_type(category_scores)

    positive_warnings = [
        question
        for question in warning_questions
        if warning_answers[question["id"]] == "はい"
    ]

    st.divider()
    st.header("あなたの診断結果")

    st.metric(
        label="睡眠セルフチェック合計点",
        value=f"{total_score}点",
        delta="72点満点",
        delta_color="off",
    )

    st.subheader(f"総合結果：{severity_title}")
    st.write(severity_message)

    st.subheader(f"主な睡眠タイプ：{sleep_type_title}")
    st.write(sleep_type_message)

    with st.expander("項目別の点数を見る"):
        for category, score in category_scores.items():
            st.write(f"**{category}：{score}点**")

    # 注意項目
    if positive_warnings:
        st.warning(
            "注意して確認したい項目に「はい」があります。"
            "点数にかかわらず、症状が続く場合は医療機関への相談を検討してください。"
        )
        for question in positive_warnings:
            st.write(f"・Q{question['id']}：{question['text']}")

        if warning_answers[22] == "はい":
            st.error(
                "運転中や仕事中に眠りそうになる場合は、事故につながるおそれがあります。"
                "眠気がある状態での運転や危険な作業は避け、早めに専門家へ相談してください。"
            )
    else:
        st.success(
            "注意項目には、現在「はい」と答えたものはありませんでした。"
        )

    # 香りの提案
    st.subheader("眠る前の香りの提案")

    if (
        aroma_interest == "香りが苦手"
        or aroma_preference == "香りは使いたくない"
        or aroma_method == "香り以外の方法を選ぶ"
    ):
        st.write(
            "香りを無理に使う必要はありません。"
            "照明を少し暗くする、深呼吸する、軽くストレッチするなど、"
            "心地よく続けられる方法を選びましょう。"
        )
    else:
        st.write(get_aroma_message(aroma_preference, aroma_method))

    st.caption(
        "精油を肌へ直接つけたり、飲んだりしないでください。"
        "持病、妊娠、服薬、アレルギーなどがある場合は、"
        "使用前に医師や薬剤師などへ確認してください。"
    )

    st.divider()
    st.caption(
        "この結果は医療上の診断ではありません。"
        "強い日中の眠気、呼吸停止、大きないびき、長く続く不眠、"
        "生活への大きな支障がある場合は、医療機関へご相談ください。"
    )
