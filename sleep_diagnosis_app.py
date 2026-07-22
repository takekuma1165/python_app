import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from datetime import date
from pathlib import Path

# 診断結果を保存するCSVファイル
DATA_FILE = Path(__file__).with_name("sleep_results.csv")

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
        "id": 5,
        "category": "生活リズム",
        "text": "寝る時間や起きる時間が、日によって大きく変わりますか？",
    },
    {
        "id": 6,
        "category": "生活リズム",
        "text": "必要だと感じる睡眠時間より、実際の睡眠時間が短いですか？",
    },
    {
        "id": 7,
        "category": "生活リズム",
        "text": "夕方以降に、30分以上うたた寝をすることがありますか？",
    },
    {
        "id": 8,
        "category": "寝つき",
        "text": "布団に入ってから眠るまで、30分以上かかることがありますか？",
    },
    {
        "id": 9,
        "category": "寝つき",
        "text": "寝る直前までスマートフォンやパソコンを見ていますか？",
    },
    {
        "id": 10,
        "category": "心配事",
        "text": "寝る前に考え事が止まらなくなることがありますか？",
    },
    {
        "id": 11,
        "category": "途中覚醒",
        "text": "夜中に何度も目が覚めることがありますか？",
    },
    {
        "id": 12,
        "category": "途中覚醒",
        "text": "トイレに行くために、夜中に目が覚めることがありますか？",
    },
    {
        "id": 13,
        "category": "途中覚醒",
        "text": "寝室の暑さ、寒さ、明るさ、音が気になることがありますか？",
    },
    {
    "id": 14,
    "category": "生活リズム",
    "text": "寝る前3時間以内に、お酒を飲むことがありますか？",
},
    {
        "id": 15,
    "category": "休養感",
    "text": "朝起きたとき、『よく眠れた』という満足が得られないことがありますか？",
},
{
    "id": 16,
    "category": "休養感",
    "text": "朝起きたあとも、身体のだるさや疲れが残ることがありますか？",
},
    {
        "id": 17,
        "category": "休養感",
        "text": "日中、集中力ややる気が続かないことがありますか？",
    },
    {
        "id": 18,
        "category": "寝つき",
        "text": "夕方以降に、コーヒー・緑茶・紅茶・エナジードリンクなどを飲むことがありますか？",
    },
    {
        "id": 19,
        "category": "生活リズム",
        "text": "寝る直前に食事や夜食をとることがありますか？",
    },
    {
        "id": 20,
    "category": "寝つき",
    "text": "寝る前に、ゆっくり過ごす時間をとれないことがありますか？",
    },
]

warning_questions = [
    {
        "id": 21,
        "text": "ご家族などから、大きないびきを指摘されたことがありますか？",
    },
    {
        "id": 22,
        "text": "寝ている間に、呼吸が止まっていると指摘されたことがありますか？",
    },
    {
        "id": 23,
        "text": "十分な睡眠時間をとっているのに、日中に強い眠気がありますか？",
    },
    {
        "id": 24,
        "text": "運転中や仕事中に、眠気で危険を感じたことがありますか？",
    },
    {
        "id": 25,
        "text": "睡眠の悩みが週3日以上あり、1か月以上続いていますか？",
    },
]

# ---------------------------------
# 診断ロジック
# ---------------------------------
def get_severity(total_score: int) -> tuple[str, str, str]:
    """100点換算した点数から、A～Dの睡眠評価を判定する。"""

    if total_score >= 80:
        return (
            "A",
            "よく眠れている状態",
            "現在の睡眠は、おおむね良好な状態です。"
            "今の生活リズムを大切にしながら、良い習慣を続けていきましょう。",
        )

    if total_score >= 60:
        return (
            "B",
            "睡眠習慣に少し注意が必要",
            "睡眠時間や寝る前の習慣に、少し気になる点があるようです。"
            "起きる時間をそろえる、夕方以降のカフェインを控えるなど、"
            "できることを一つから始めてみましょう。",
        )

    if total_score >= 40:
        return (
            "C",
            "睡眠の見直しが必要",
            "寝つきや夜中の目覚め、日中の眠気など、"
            "いくつかの睡眠の悩みが重なっている可能性があります。"
            "点数が低かった項目を意識して、生活習慣を少しずつ見直してみましょう。",
        )

    return (
        "D",
        "専門家への相談を検討したい状態",
        "睡眠の悩みが、日中の生活にも影響している可能性があります。"
        "症状が長く続いている場合や、生活習慣を見直しても改善しない場合は、"
        "かかりつけ医や睡眠を扱う医療機関への相談を検討しましょう。",
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
            "眠ってもすっきりしないタイプ",
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

def get_sleep_improvement_advice(answers: dict) -> list[str]:
    """回答内容に合わせて、眠りを整える提案を作る。"""

    advice = []

    # 生活リズム
    if (
        score_options[answers[5]] >= 2
        or score_options[answers[6]] >= 2
    ):
        advice.append(
            "まずは毎朝の起きる時間を、できる範囲でそろえてみましょう。"
            "朝にカーテンを開けて光を浴びると、生活リズムを整えやすくなります。"
        )

    # 夕方以降のうたた寝
    if score_options[answers[7]] >= 2:
        advice.append(
            "夕方以降の長いうたた寝は、夜の寝つきを妨げることがあります。"
            "昼寝をする場合は、遅い時間を避けて短めにしてみましょう。"
        )

    # 寝つき
    if (
        score_options[answers[8]] >= 2
        or score_options[answers[20]] >= 2
    ):
        advice.append(
            "寝る前に、深呼吸や軽いストレッチなど、"
            "気持ちを落ち着ける時間を作ってみましょう。"
        )

    # スマートフォン
    if score_options[answers[9]] >= 2:
        advice.append(
            "寝る前はスマートフォンやパソコンを見る時間を少し減らし、"
            "照明を暗めにして過ごしてみましょう。"
        )

    # 考え事
    if score_options[answers[10]] >= 2:
        advice.append(
            "寝る前に考え事が止まらないときは、明日の予定や不安を紙に書き出してみましょう。"
            "頭の中だけで考え続けないことが、気持ちの切り替えにつながります。"
        )

    # 夜中の目覚め
    if (
        score_options[answers[11]] >= 2
        or score_options[answers[12]] >= 2
    ):
        advice.append(
            "夜中に目が覚めやすい場合は、寝室環境や寝る前の水分量、"
            "夜間のトイレの回数などを一度見直してみましょう。"
        )

    # 寝室環境
    if score_options[answers[13]] >= 2:
        advice.append(
            "寝室の明るさ、音、室温、寝具を確認し、"
            "暗く静かで心地よい環境を作ってみましょう。"
        )

    # お酒
    if score_options[answers[14]] >= 1:
        advice.append(
            "お酒は一時的に眠くなっても、夜中に目が覚める原因になることがあります。"
            "眠るためのお酒は控えることから始めてみましょう。"
        )

    # 朝のすっきり感
    if (
        score_options[answers[15]] >= 2
        or score_options[answers[16]] >= 2
        or score_options[answers[17]] >= 2
    ):
        advice.append(
            "朝すっきりしない場合は、睡眠時間だけでなく、日中の活動量や朝の光、"
            "寝る前の過ごし方も見直してみましょう。"
        )

    # カフェイン
    if score_options[answers[18]] >= 2:
        advice.append(
            "夕方以降は、コーヒー・緑茶・紅茶・エナジードリンクを控え、"
            "カフェインを含まない飲み物に替えてみましょう。"
        )

    # 夜食
    if score_options[answers[19]] >= 2:
        advice.append(
            "寝る直前の食事や夜食は避け、"
            "夕食から就寝まで少し時間を空けてみましょう。"
        )

    if not advice:
        advice.append(
            "現在の生活リズムを大切にしながら、"
            "朝の光、適度な運動、規則正しい食事を続けていきましょう。"
        )

    return advice[:4]

def save_sleep_result(
    name: str,
    age: int,
    answer_date,
    total_score: int,
    severity_grade: str,
    severity_title: str,
    sleep_type_title: str,
    warning_count: int,
) -> None:
    """今回の診断結果をCSVへ保存する。"""

    new_result = pd.DataFrame(
        [
            {
                "氏名": name.strip(),
                "年齢": int(age),
                "回答日": answer_date.isoformat(),
                "睡眠スコア": total_score,
                "評価": severity_grade,
                "睡眠状態": severity_title,
                "睡眠タイプ": sleep_type_title,
                "注意項目数": warning_count,
            }
        ]
    )

    if DATA_FILE.exists():
        saved_results = pd.read_csv(
            DATA_FILE,
            encoding="utf-8-sig",
        )

        saved_results = pd.concat(
            [saved_results, new_result],
            ignore_index=True,
        )
    else:
        saved_results = new_result

    saved_results.to_csv(
        DATA_FILE,
        index=False,
        encoding="utf-8-sig",
    )


def load_person_history(name: str) -> pd.DataFrame:
    """同じ氏名で保存された過去の結果を読み込む。"""

    if not DATA_FILE.exists():
        return pd.DataFrame()

    saved_results = pd.read_csv(
        DATA_FILE,
        encoding="utf-8-sig",
    )

    person_history = saved_results[
        saved_results["氏名"].astype(str).str.strip()
        == name.strip()
    ].copy()

    if person_history.empty:
        return person_history

    person_history["回答日"] = pd.to_datetime(
        person_history["回答日"],
        errors="coerce",
    )

    person_history = person_history.dropna(
        subset=["回答日"]
    )

    return person_history.sort_values("回答日")

def create_sleep_radar_chart(category_scores: dict):
    """睡眠の整い度をレーダーチャート用に変換する。"""

    category_max_scores = {
    "生活リズム": 20,
    "寝つき": 16,
    "途中覚醒": 12,
    "休養感": 12,
    "心配事": 4,
    }

    categories = list(category_max_scores.keys())

    # もとの category_scores は「高いほど悩みが多い」
    # ここでは 0～100 に換算したあと、100 から引いて
    # 「高いほど良い」に変換する
    good_percentages = []

    for category in categories:
        bad_percent = round(
            category_scores[category]
            / category_max_scores[category]
            * 100
        )
        good_percent = 100 - bad_percent
        good_percentages.append(good_percent)

    # 最後に最初の項目をもう一度入れて、線を閉じる
    chart_categories = categories + [categories[0]]
    chart_values = good_percentages + [good_percentages[0]]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=chart_values,
            theta=chart_categories,
            fill="toself",
            mode="lines+markers",
            name="睡眠の整い度",
            hovertemplate="%{theta}：%{r}点<extra></extra>",
        )
    )

    fig.update_layout(
        polar={
            "radialaxis": {
                "visible": True,
                "range": [0, 100],
                "tickvals": [0, 20, 40, 60, 80, 100],
            }
        },
        showlegend=False,
        height=480,
        margin={
            "l": 60,
            "r": 60,
            "t": 40,
            "b": 40,
        },
    )

    return fig, categories, good_percentages

# ---------------------------------
# 入力フォーム
# ---------------------------------
with st.form("sleep_check_form"):
    st.subheader("回答者情報")

    name = st.text_input(
        "氏名",
        placeholder="例：山田 花子",
    )

    age = st.number_input(
        "年齢",
        min_value=1,
        max_value=120,
        value=60,
        step=1,
    )

    answer_date = st.date_input(
        "アンケート回答日",
        value=date.today(),
    )

    st.caption(
        "診断結果は、このアプリと同じフォルダーに保存されます。"
    )

    st.subheader("今いちばん困っていること")

    main_sleep_problem = st.radio(
        "Q4．今、睡眠でいちばん困っていることは何ですか？",
        options=[
            "なかなか寝つけない",
            "夜中に何度も目が覚める",
            "朝早く目が覚めてしまう",
            "寝ても疲れが取れない",
            "日中に眠くなる",
            "特に困っていないが、睡眠の質をさらに高めたい",
        ],
        key="main_sleep_problem",
    )

    st.divider()

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
    st.subheader("2．睡眠について気をつけたいサイン")
    st.caption(
    "以下は総合点には含まれません。"
    "「はい」がある場合は、必要に応じて医療機関への相談も検討しましょう。"
)

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
        "診断結果を表示して保存",
        type="primary",
        use_container_width=True,
    )

# ---------------------------------
# 結果表示
# ---------------------------------
if submitted:
    if not name.strip():
        st.error("氏名を入力してください。")
        st.stop()

    raw_score = sum(
        score_options[answer]
        for answer in answers.values()
    )

    # 100点に近いほど良い睡眠状態
    total_score = round(
        (64 - raw_score) / 64 * 100
    )

    # カテゴリーごとの点数を入れる箱を作る
    category_scores = {
        "生活リズム": 0,
        "寝つき": 0,
        "途中覚醒": 0,
        "休養感": 0,
        "心配事": 0,
    }

    # 各設問の点数をカテゴリーごとに合計する
    for question in questions:
        category = question["category"]
        category_scores[category] += score_options[
            answers[question["id"]]
        ]

    severity_grade, severity_title, severity_message = get_severity(
        total_score
    )

    sleep_type_title, sleep_type_message = get_sleep_type(
        category_scores
    )

    positive_warnings = [
        question
        for question in warning_questions
        if warning_answers[question["id"]] == "はい"
    ]

    warning_count = len(positive_warnings)

    save_sleep_result(
        name=name,
        age=age,
        answer_date=answer_date,
        total_score=total_score,
        severity_grade=severity_grade,
        severity_title=severity_title,
        sleep_type_title=sleep_type_title,
        warning_count=warning_count,
    )

    st.success("今回の診断結果を保存しました。")

    st.divider()
    st.header("あなたの診断結果")

    st.metric(
        label="睡眠セルフチェック合計点",
        value=f"{total_score}点",
        delta="100点満点",
        delta_color="off",
    )

    st.progress(total_score / 100)

    st.subheader(f"総合評価：{severity_grade}評価")
    
    st.markdown(f"### {severity_title}")
    st.write(severity_message)

    st.subheader(f"主な睡眠タイプ：{sleep_type_title}")
    st.write(sleep_type_message)
    st.write(f"**最も気になっている悩み：{main_sleep_problem}**")

    with st.expander(
        "睡眠の悩み別の結果を見る",
        expanded=True,
    ):
        st.caption(
            "総合点は高いほど良い状態です。"
            "このレーダーチャートも、外側に広がるほど"
            "その分野の状態が良いことを示します。"
        )

        radar_chart, radar_categories, good_percentages = (
            create_sleep_radar_chart(category_scores)
        )

        st.plotly_chart(
            radar_chart,
            use_container_width=True,
            key="sleep_radar_chart",
        )

        st.write("#### 睡眠の整い度")

        for category, percentage in zip(
            radar_categories,
            good_percentages,
        ):
            st.write(
                f"**{category}：{percentage}点**"
            )

    # 注意項目
    if positive_warnings:
        st.warning(
            "注意して確認したい項目に「はい」があります。"
            "点数にかかわらず、症状が続く場合は医療機関への相談を検討してください。"
        )
        for question in positive_warnings:
            st.write(f"・Q{question['id']}：{question['text']}")

        if warning_answers[24] == "はい":
            st.error(
                "運転中や仕事中に眠りそうになる場合は、事故につながる可能性があります。"
                "眠気がある状態での運転や危険な作業は避け、早めに専門家へ相談してください。"
            )
    else:
        st.success(
            "注意項目には、現在「はい」と答えたものはありませんでした。"
        )

 # 香り以外の提案
    st.subheader("眠りの質を上げるための提案")

    sleep_advice = get_sleep_improvement_advice(answers)

    st.write(
        "すべてを一度に変える必要はありません。"
        "続けやすいものを一つ選んで試してみましょう。"
    )

    for number, advice in enumerate(sleep_advice, start=1):
        st.markdown(f"**{number}．{advice}**")

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

    st.divider()
    st.header("過去の結果との比較")

    history = load_person_history(name)

    if history.empty:
        st.info("過去の診断結果はありません。")

    else:
        st.write(
            f"{name}さんの診断結果を表示しています。"
        )

        if len(history) >= 2:
            latest_score = int(
                history.iloc[-1]["睡眠スコア"]
            )

            previous_score = int(
                history.iloc[-2]["睡眠スコア"]
            )

            score_difference = (
                latest_score - previous_score
            )

            if score_difference > 0:
                st.success(
                    f"前回より{score_difference}点上がりました。"
                )

            elif score_difference < 0:
                st.warning(
                    f"前回より{abs(score_difference)}点下がりました。"
                )

            else:
                st.info(
                    "前回と同じ点数です。"
                )

        if len(history) == 1:
            st.info(
                "今回が最初の記録です。"
                "次回から結果を比較できます。"
            )

        chart_data = history[
            ["回答日", "睡眠スコア"]
        ].copy()

        chart_data = chart_data.set_index(
            "回答日"
        )

        st.subheader("睡眠スコアの変化")
        st.line_chart(chart_data)

        display_history = history[
            [
                "回答日",
                "年齢",
                "睡眠スコア",
                "評価",
                "睡眠状態",
                "睡眠タイプ",
                "注意項目数",
            ]
        ].copy()

        display_history["回答日"] = (
            display_history["回答日"]
            .dt.strftime("%Y年%m月%d日")
        )

        st.subheader("これまでの記録")

        st.dataframe(
            display_history,
            hide_index=True,
            use_container_width=True,
        )

        csv_data = display_history.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            label="自分の記録をCSVで保存",
            data=csv_data,
            file_name=f"{name}_睡眠診断記録.csv",
            mime="text/csv",
        )