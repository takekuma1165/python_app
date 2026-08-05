from __future__ import annotations

from datetime import date, datetime
import random
from zoneinfo import ZoneInfo

import streamlit as st


# 11・22・33をマスターナンバーとして残します。
MASTER_NUMBERS = {11, 22, 33}


AFFIRMATION_DATA = {
    1: {
        "theme": "始まり・自立・行動",
        "affirmations": [
            "私は、自分の力を信じて新しい一歩を踏み出します。",
            "私は、今日できる小さな行動から未来をつくります。",
            "私は、自分らしい選択を大切にします。",
        ],
        "action": "先延ばしにしていたことを一つだけ始めてみましょう。",
    },
    2: {
        "theme": "調和・協力・受容",
        "affirmations": [
            "私は、焦らず穏やかな流れを信頼します。",
            "私は、人とのつながりを大切にしながら進みます。",
            "私は、自分と相手の気持ちを優しく受け止めます。",
        ],
        "action": "身近な人に感謝の言葉を一つ伝えてみましょう。",
    },
    3: {
        "theme": "表現・創造・喜び",
        "affirmations": [
            "私は、自分の言葉と笑顔で喜びを広げます。",
            "私は、自由な発想を楽しみます。",
            "私は、心に浮かんだ思いを素直に表現します。",
        ],
        "action": "文章、会話、写真などで気持ちを表現してみましょう。",
    },
    4: {
        "theme": "安定・継続・基盤",
        "affirmations": [
            "私は、一つずつ丁寧に積み重ねています。",
            "私は、落ち着いて自分の土台を整えます。",
            "私は、毎日の小さな習慣を力に変えます。",
        ],
        "action": "机の上や予定表など、一か所だけ整えてみましょう。",
    },
    5: {
        "theme": "変化・自由・挑戦",
        "affirmations": [
            "私は、変化を新しい可能性として受け入れます。",
            "私は、柔軟な心で今日を楽しみます。",
            "私は、好奇心に従って新しい経験を選びます。",
        ],
        "action": "いつもと違う道、方法、選択を一つ試してみましょう。",
    },
    6: {
        "theme": "愛・家庭・思いやり",
        "affirmations": [
            "私は、自分にも周りの人にも優しさを向けます。",
            "私は、安心できる時間と場所を大切にします。",
            "私は、愛情を受け取り、素直に分かち合います。",
        ],
        "action": "自分をいたわる時間を10分だけつくりましょう。",
    },
    7: {
        "theme": "内省・学び・直感",
        "affirmations": [
            "私は、静かな時間の中で本当の気持ちに気づきます。",
            "私は、自分の直感と内なる知恵を信頼します。",
            "私は、答えを急がず、深く学ぶ時間を大切にします。",
        ],
        "action": "5分だけ静かに過ごし、感じたことを書き留めましょう。",
    },
    8: {
        "theme": "豊かさ・達成・責任",
        "affirmations": [
            "私は、自分の力を豊かさへと結びつけます。",
            "私は、努力に見合う成果を受け取る価値があります。",
            "私は、目的を持って落ち着いて行動します。",
        ],
        "action": "今日の最優先事項を一つ決め、先に取り組みましょう。",
    },
    9: {
        "theme": "完結・手放し・奉仕",
        "affirmations": [
            "私は、役目を終えたものを感謝とともに手放します。",
            "私は、過去の経験を優しさと知恵に変えます。",
            "私は、広い心で自分と周りの人を受け入れます。",
        ],
        "action": "不要な物、予定、思い込みを一つ手放してみましょう。",
    },
    11: {
        "theme": "直感・ひらめき・精神性",
        "affirmations": [
            "私は、心に届くひらめきを大切にします。",
            "私は、自分の感性を信じ、希望を言葉にします。",
            "私は、内側から届く静かなメッセージを受け取ります。",
        ],
        "action": "思いついたことを評価せず、まずメモしておきましょう。",
    },
    22: {
        "theme": "理想の実現・構築・社会貢献",
        "affirmations": [
            "私は、大きな理想を現実的な一歩へ変えていきます。",
            "私は、長い目で価値あるものを育てています。",
            "私は、自分の力を周りの幸せにも役立てます。",
        ],
        "action": "大きな目標を、今日できる一つの作業に分けましょう。",
    },
    33: {
        "theme": "無条件の愛・癒やし・奉仕",
        "affirmations": [
            "私は、優しさを大切にしながら自分自身も守ります。",
            "私は、愛と思いやりを無理のない形で分かち合います。",
            "私は、自分を満たし、その温かさを周りへ広げます。",
        ],
        "action": "人のためだけでなく、自分にも優しい選択をしましょう。",
    },
}


LIFE_PATH_MESSAGES = {
    1: "自分で道を切り開く力を持つ人",
    2: "人との調和やつながりを育てる人",
    3: "表現や創造性で明るさを届ける人",
    4: "誠実な積み重ねで土台をつくる人",
    5: "変化を楽しみながら可能性を広げる人",
    6: "愛情と責任感で人を支える人",
    7: "深く考え、本質を探究する人",
    8: "現実を動かし、成果へつなげる人",
    9: "広い視点と優しさで人に尽くす人",
    11: "豊かな感性と直感で希望を示す人",
    22: "大きな構想を現実に築き上げる人",
    33: "深い愛と癒やしを分かち合う人",
}


def reduce_number(value: int, keep_master: bool = True) -> int:
    """数値を1桁に縮約。keep_master=Trueなら11・22・33は残す。"""
    value = abs(int(value))
    while value > 9:
        if keep_master and value in MASTER_NUMBERS:
            return value
        value = sum(int(digit) for digit in str(value))
    return value


def calculate_life_path(birth_date: date) -> int:
    """生年月日の全数字を足してライフパスナンバーを計算。"""
    digits = birth_date.strftime("%Y%m%d")
    return reduce_number(sum(int(digit) for digit in digits))


def calculate_personal_numbers(
    birth_date: date,
    target_date: date,
) -> tuple[int, int, int]:
    """
    パーソナルイヤー、パーソナルマンス、パーソナルデーを計算。
    年：誕生月 + 誕生日 + 対象年の数字合計
    月：パーソナルイヤー + 対象月
    日：パーソナルマンス + 対象日
    """
    year_number = sum(int(digit) for digit in str(target_date.year))
    personal_year = reduce_number(birth_date.month + birth_date.day + year_number)
    personal_month = reduce_number(personal_year + target_date.month)
    personal_day = reduce_number(personal_month + target_date.day)
    return personal_year, personal_month, personal_day


def select_daily_affirmation(
    personal_day: int,
    target_date: date,
    name: str,
    life_path: int,
) -> str:
    """同じ日・同じ利用者には同じ文章を表示。"""
    data = AFFIRMATION_DATA[personal_day]
    seed_text = f"{target_date.isoformat()}-{name.strip()}-{life_path}-{personal_day}"
    seed = sum((index + 1) * ord(char) for index, char in enumerate(seed_text))
    generator = random.Random(seed)
    return generator.choice(data["affirmations"])


st.set_page_config(
    page_title="毎日の数秘術アファメーション",
    page_icon="✨",
    layout="centered",
)

st.title("✨ 毎日の数秘術アファメーション")
st.write(
    "生年月日と日付から数秘ナンバーを計算し、"
    "その日のテーマに合わせた言葉を表示します。"
)

with st.form("numerology_form"):
    name = st.text_input(
        "お名前またはニックネーム",
        placeholder="例：みやび",
    )

    birth_date = st.date_input(
        "生年月日",
        value=date(1970, 1, 1),
        min_value=date(1900, 1, 1),
        max_value=date.today(),
    )

    today_japan = datetime.now(ZoneInfo("Asia/Tokyo")).date()
    target_date = st.date_input(
        "アファメーションを表示する日",
        value=today_japan,
        min_value=date(1900, 1, 1),
        max_value=date(2100, 12, 31),
    )

    submitted = st.form_submit_button(
        "今日のメッセージを見る",
        use_container_width=True,
    )


if submitted:
    life_path = calculate_life_path(birth_date)
    personal_year, personal_month, personal_day = calculate_personal_numbers(
        birth_date,
        target_date,
    )

    day_data = AFFIRMATION_DATA[personal_day]
    affirmation = select_daily_affirmation(
        personal_day=personal_day,
        target_date=target_date,
        name=name,
        life_path=life_path,
    )

    display_name = name.strip() or "あなた"

    st.divider()
    st.caption(target_date.strftime("%Y年%m月%d日"))

    st.subheader(f"{display_name}の今日のアファメーション")
    st.success(f"「{affirmation}」")

    st.metric("今日のパーソナルデーナンバー", personal_day)
    st.write(f"**今日のテーマ：** {day_data['theme']}")
    st.info(f"**今日の小さな行動：** {day_data['action']}")

    with st.expander("数秘ナンバーの詳細を見る"):
        col1, col2, col3 = st.columns(3)
        col1.metric("ライフパス", life_path)
        col2.metric("パーソナルイヤー", personal_year)
        col3.metric("パーソナルマンス", personal_month)

        st.write(
            f"**ライフパス{life_path}：** "
            f"{LIFE_PATH_MESSAGES.get(life_path, '自分らしい可能性を育てる人')}"
        )

    st.caption(
        "※数秘術は科学的な診断ではありません。"
        "毎日を前向きに振り返るためのヒントとしてお楽しみください。"
    )
