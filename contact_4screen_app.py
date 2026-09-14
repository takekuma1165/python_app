import csv
import html
import os

import streamlit as st

st.set_page_config(
    page_title="お問い合わせフォーム",
    page_icon="✉️",
    layout="centered",
)

# =========================
# 初期設定
# =========================
if "page" not in st.session_state:
    st.session_state.page = "login"

if "login_data" not in st.session_state:
    st.session_state.login_data = {}

if "contact_data" not in st.session_state:
    st.session_state.contact_data = {}

# =========================
# デザイン
# =========================
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f4efe9;
        color: #5f4b3f;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        max-width: 920px;
        padding-top: 2.5rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #6f4d3e !important;
        text-align: center;
        font-family: Georgia, "Times New Roman", serif;
        font-weight: 500;
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-baseweb="select"] > div {
        background-color: #fbfaf8 !important;
        border-color: #ddd2c8 !important;
        border-radius: 8px !important;
    }

    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus {
        border-color: #9b7f6d !important;
        box-shadow: 0 0 0 1px #9b7f6d !important;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        background-color: #806d60;
        color: white;
        border: none;
        border-radius: 7px;
        padding: 0.6rem 1.6rem;
        font-size: 1rem;
        min-height: 42px;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background-color: #6f5d52;
        color: white;
        border: none;
    }

    .required {
        color: #c67e72;
        font-weight: 700;
    }

    .confirm-table {
        width: 100%;
        border-collapse: collapse;
        background: white;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(90, 70, 55, 0.06);
        margin: 1.5rem 0;
    }

    .confirm-table th {
        width: 30%;
        background-color: #c8b4a5;
        color: white;
        text-align: left;
        vertical-align: top;
        padding: 14px 18px;
        border-bottom: 1px solid #eadfd6;
    }

    .confirm-table td {
        background-color: #fff;
        color: #5f4b3f;
        padding: 14px 18px;
        border-bottom: 1px solid #eadfd6;
        word-break: break-word;
    }

    .thanks-wrap {
        text-align: center;
        padding: 90px 10px 70px;
        position: relative;
        overflow: hidden;
    }

    .thanks-bg {
        font-family: Georgia, "Times New Roman", serif;
        font-size: clamp(70px, 15vw, 180px);
        color: rgba(223, 193, 115, 0.22);
        line-height: 0.85;
        margin-bottom: -55px;
        white-space: nowrap;
    }

    .thanks-message {
        position: relative;
        z-index: 2;
        font-size: 1.35rem;
        color: #7d4c2f;
        margin-bottom: 1.5rem;
    }

    .small-note {
        color: #8c796d;
        font-size: 0.9rem;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# 共通関数
# =========================
def go(page_name):
    st.session_state.page = page_name
    st.rerun()


def safe(value):
    return html.escape(str(value or ""))


def save_contact_csv(data):
    csv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "contact_submissions.csv",
    )
    fieldnames = [
        "お名前",
        "性別",
        "メールアドレス",
        "電話番号",
        "住所",
        "建物名",
        "お問い合わせの種類",
        "タグ",
        "お問い合わせ内容",
    ]
    row = {
        "お名前": f"{data.get('last_name', '')} {data.get('first_name', '')}".strip(),
        "性別": data.get("gender", ""),
        "メールアドレス": data.get("email", ""),
        "電話番号": data.get("phone", ""),
        "住所": data.get("address", ""),
        "建物名": data.get("building", ""),
        "お問い合わせの種類": data.get("inquiry_type", ""),
        "タグ": "、".join(data.get("tags", [])),
        "お問い合わせ内容": data.get("message", ""),
    }

    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists or os.path.getsize(csv_path) == 0:
            writer.writeheader()
        writer.writerow(row)


# =========================
# 1. ログイン / 登録画面
# =========================
if st.session_state.page == "login":
    st.markdown("<h1>Login</h1>", unsafe_allow_html=True)

    with st.form("login_form"):
        name = st.text_input(
            "お名前",
            value=st.session_state.login_data.get("name", ""),
            placeholder="例：山田 太郎",
        )

        email = st.text_input(
            "メールアドレス",
            value=st.session_state.login_data.get("email", ""),
            placeholder="email@example.com",
        )

        password = st.text_input(
            "パスワード",
            type="password",
            placeholder="password",
        )

        password_confirm = st.text_input(
            "パスワード確認",
            type="password",
            placeholder="password",
        )

        submitted = st.form_submit_button("ログイン", use_container_width=True)

        if submitted:
            errors = []

            if not name.strip():
                errors.append("お名前を入力してください。")

            if not email.strip() or "@" not in email:
                errors.append("正しいメールアドレスを入力してください。")

            if len(password) < 6:
                errors.append("パスワードは6文字以上で入力してください。")

            if password != password_confirm:
                errors.append("パスワードが一致していません。")

            if errors:
                for error in errors:
                    st.error(error)
            else:
                st.session_state.login_data = {
                    "name": name.strip(),
                    "email": email.strip(),
                }
                go("contact")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        '<p class="small-note">※ このサンプルでは本物の会員認証やデータベース保存は行いません。</p>',
        unsafe_allow_html=True,
    )

# =========================
# 2. お問い合わせ入力画面
# =========================
elif st.session_state.page == "contact":
    st.markdown("<h1>Contact</h1>", unsafe_allow_html=True)

    data = st.session_state.contact_data

    with st.form("contact_form"):
        st.markdown("### お問い合わせ情報")

        c1, c2 = st.columns(2)
        with c1:
            last_name = st.text_input(
                "姓 ＊",
                value=data.get("last_name", ""),
                placeholder="例：山田",
            )
        with c2:
            first_name = st.text_input(
                "名 ＊",
                value=data.get("first_name", ""),
                placeholder="例：太郎",
            )

        gender = st.radio(
            "性別 ＊",
            ["男性", "女性", "その他"],
            index=["男性", "女性", "その他"].index(data.get("gender", "男性")),
            horizontal=True,
        )

        email = st.text_input(
            "メールアドレス ＊",
            value=data.get(
                "email",
                st.session_state.login_data.get("email", ""),
            ),
            placeholder="例：test@example.com",
        )

        phone = st.text_input(
            "電話番号 ＊",
            value=data.get("phone", ""),
            placeholder="例：09012345678",
        )

        address = st.text_input(
            "住所 ＊",
            value=data.get("address", ""),
            placeholder="例：東京都渋谷区千駄ヶ谷1-2-3",
        )

        building = st.text_input(
            "建物名",
            value=data.get("building", ""),
            placeholder="例：千駄ヶ谷マンション305",
        )

        inquiry_types = [
            "選択してください",
            "ご質問",
            "ご要望",
            "不具合報告",
            "ご意見",
            "その他",
        ]

        current_type = data.get("inquiry_type", "選択してください")
        inquiry_type = st.selectbox(
            "お問い合わせの種類 ＊",
            inquiry_types,
            index=inquiry_types.index(current_type)
            if current_type in inquiry_types
            else 0,
        )

        tags = st.multiselect(
            "タグ",
            ["質問", "要望", "不具合報告", "ご意見", "その他"],
            default=data.get("tags", []),
        )

        message = st.text_area(
            "お問い合わせ内容 ＊",
            value=data.get("message", ""),
            placeholder="お問い合わせ内容をご記入ください",
            height=180,
        )

        confirmed = st.form_submit_button(
            "確認画面へ",
            use_container_width=True,
        )

        if confirmed:
            errors = []

            if not last_name.strip() or not first_name.strip():
                errors.append("お名前を入力してください。")

            if not email.strip() or "@" not in email:
                errors.append("正しいメールアドレスを入力してください。")

            if not phone.strip():
                errors.append("電話番号を入力してください。")

            if not address.strip():
                errors.append("住所を入力してください。")

            if inquiry_type == "選択してください":
                errors.append("お問い合わせの種類を選択してください。")

            if not message.strip():
                errors.append("お問い合わせ内容を入力してください。")

            if errors:
                for error in errors:
                    st.error(error)
            else:
                st.session_state.contact_data = {
                    "last_name": last_name.strip(),
                    "first_name": first_name.strip(),
                    "gender": gender,
                    "email": email.strip(),
                    "phone": phone.strip(),
                    "address": address.strip(),
                    "building": building.strip(),
                    "inquiry_type": inquiry_type,
                    "tags": tags,
                    "message": message.strip(),
                }
                go("confirm")

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("← ログイン画面に戻る"):
        go("login")

# =========================
# 3. 確認画面
# =========================
elif st.session_state.page == "confirm":
    st.markdown("<h1>Confirm</h1>", unsafe_allow_html=True)

    d = st.session_state.contact_data

    rows = [
        ("お名前", f"{safe(d.get('last_name'))} {safe(d.get('first_name'))}"),
        ("性別", safe(d.get("gender"))),
        ("メールアドレス", safe(d.get("email"))),
        ("電話番号", safe(d.get("phone"))),
        ("住所", safe(d.get("address"))),
        ("建物名", safe(d.get("building")) or "―"),
        ("お問い合わせの種類", safe(d.get("inquiry_type"))),
        ("タグ", safe("、".join(d.get("tags", []))) or "―"),
        ("お問い合わせ内容", safe(d.get("message")).replace("\n", "<br>")),
    ]

    table_html = '<table class="confirm-table">'
    for label, value in rows:
        table_html += f"<tr><th>{label}</th><td>{value}</td></tr>"
    table_html += "</table>"

    st.markdown(table_html, unsafe_allow_html=True)

    left, right = st.columns(2)

    with left:
        if st.button("送信", use_container_width=True):
            save_contact_csv(d)
            go("complete")

    with right:
        if st.button("修正", use_container_width=True):
            go("contact")

# =========================
# 4. 完了画面
# =========================
elif st.session_state.page == "complete":
    st.markdown(
        """
        <div class="thanks-wrap">
            <div class="thanks-bg">Thank you</div>
            <div class="thanks-message">
                お問い合わせありがとうございました
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("HOME", use_container_width=True):
        st.session_state.login_data = {}
        st.session_state.contact_data = {}
        go("login")