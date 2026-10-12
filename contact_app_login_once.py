import csv

import html

import io

import os

import sqlite3

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

if "admin_authenticated" not in st.session_state:

    st.session_state.admin_authenticated = False

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

def get_db_path():

    return os.path.join(

        os.path.dirname(os.path.abspath(__file__)),

        "contact.db",

    )

def init_db():

    """SQLiteデータベースとcontactsテーブルを初回起動時に作成します。"""

    conn = sqlite3.connect(get_db_path())

    cursor = conn.cursor()

    cursor.execute(

        """

        CREATE TABLE IF NOT EXISTS contacts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            last_name TEXT NOT NULL,

            first_name TEXT NOT NULL,

            gender TEXT NOT NULL,

            email TEXT NOT NULL,

            phone TEXT NOT NULL,

            address TEXT NOT NULL,

            building TEXT,

            inquiry_type TEXT NOT NULL,

            tags TEXT,

            message TEXT NOT NULL,

            status TEXT NOT NULL DEFAULT '未対応',

            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

        )

        """

    )

    conn.commit()

    conn.close()

def save_contact_db(data):

    """お問い合わせ内容をSQLiteに保存し、保存したIDを返します。"""

    db_path = get_db_path()

    with sqlite3.connect(db_path, timeout=30) as conn:

        cursor = conn.cursor()

        cursor.execute(

            """

            INSERT INTO contacts (

                last_name,

                first_name,

                gender,

                email,

                phone,

                address,

                building,

                inquiry_type,

                tags,

                message

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            """,

            (

                data.get("last_name", ""),

                data.get("first_name", ""),

                data.get("gender", ""),

                data.get("email", ""),

                data.get("phone", ""),

                data.get("address", ""),

                data.get("building", ""),

                data.get("inquiry_type", ""),

                "、".join(data.get("tags", [])),

                data.get("message", ""),

            ),

        )

        conn.commit()

        return cursor.lastrowid

def get_admin_password():

    """管理者パスワードを取得します。

    Streamlit Secrets の ADMIN_PASSWORD を優先し、なければ環境変数を確認します。

    学習・ローカル実行用として最後に admin123 を使用します。

    公開時は必ず変更してください。

    """

    try:

        secret_password = st.secrets.get("ADMIN_PASSWORD", "")

        if secret_password:

            return str(secret_password)

    except Exception:

        pass

    return os.environ.get("ADMIN_PASSWORD", "admin123")

def fetch_contacts(search_text="", status_filter="すべて"):

    """検索条件に一致するお問い合わせを新しい順に取得します。"""

    conn = sqlite3.connect(get_db_path())

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    sql = "SELECT * FROM contacts WHERE 1=1"

    params = []

    if status_filter in ("未対応", "対応済み"):

        sql += " AND status = ?"

        params.append(status_filter)

    keyword = search_text.strip()

    if keyword:

        like = f"%{keyword}%"

        sql += """

            AND (

                CAST(id AS TEXT) LIKE ? OR

                last_name LIKE ? OR

                first_name LIKE ? OR

                email LIKE ? OR

                phone LIKE ? OR

                address LIKE ? OR

                COALESCE(building, '') LIKE ? OR

                inquiry_type LIKE ? OR

                COALESCE(tags, '') LIKE ? OR

                message LIKE ? OR

                status LIKE ? OR

                created_at LIKE ?

            )

        """

        params.extend([like] * 12)

    sql += " ORDER BY id DESC"

    cursor.execute(sql, params)

    rows = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return rows

def update_contact_status(contact_id, new_status):

    """指定したお問い合わせの対応状況を更新します。"""

    if new_status not in ("未対応", "対応済み"):

        raise ValueError("不正なステータスです。")

    conn = sqlite3.connect(get_db_path())

    cursor = conn.cursor()

    cursor.execute(

        "UPDATE contacts SET status = ? WHERE id = ?",

        (new_status, int(contact_id)),

    )

    conn.commit()

    conn.close()

def delete_contact(contact_id):

    """指定したお問い合わせを削除します。"""

    conn = sqlite3.connect(get_db_path())

    cursor = conn.cursor()

    cursor.execute("DELETE FROM contacts WHERE id = ?", (int(contact_id),))

    conn.commit()

    conn.close()

def contacts_to_csv(rows):

    """お問い合わせ一覧をExcelでも開きやすいCSV(bytes)に変換します。"""

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(

        [

            "ID",

            "姓",

            "名",

            "性別",

            "メールアドレス",

            "電話番号",

            "住所",

            "建物名",

            "お問い合わせの種類",

            "タグ",

            "お問い合わせ内容",

            "対応状況",

            "送信日時",

        ]

    )

    for row in rows:

        writer.writerow(

            [

                row.get("id", ""),

                row.get("last_name", ""),

                row.get("first_name", ""),

                row.get("gender", ""),

                row.get("email", ""),

                row.get("phone", ""),

                row.get("address", ""),

                row.get("building", ""),

                row.get("inquiry_type", ""),

                row.get("tags", ""),

                row.get("message", ""),

                row.get("status", ""),

                row.get("created_at", ""),

            ]

        )

    return output.getvalue().encode("utf-8-sig")

# アプリ起動時にデータベースを準備

init_db()

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

        submitted = st.form_submit_button("ログイン", use_container_width=True)

        if submitted:

            errors = []

            if not name.strip():

                errors.append("お名前を入力してください。")

            if not email.strip() or "@" not in email:

                errors.append("正しいメールアドレスを入力してください。")

            if len(password) < 6:

                errors.append("パスワードは6文字以上で入力してください。")

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

        '<p class="small-note">※ このサンプルでは本物の会員認証は行いません。お問い合わせ内容はSQLiteデータベースに保存されます。</p>',

        unsafe_allow_html=True,

    )

    st.divider()

    if st.button("🔐 管理者画面", use_container_width=True):

        go("admin_login")

# =========================

# 管理者ログイン画面

# =========================

elif st.session_state.page == "admin_login":

    st.markdown("<h1>Admin Login</h1>", unsafe_allow_html=True)

    with st.form("admin_login_form"):

        admin_password = st.text_input(

            "管理者パスワード",

            type="password",

            placeholder="管理者パスワードを入力",

        )

        admin_login = st.form_submit_button(

            "管理者としてログイン",

            use_container_width=True,

        )

        if admin_login:

            if admin_password == get_admin_password():

                st.session_state.admin_authenticated = True

                go("admin")

            else:

                st.error("管理者パスワードが違います。")

    st.info(

        "ローカル学習用の初期パスワードは admin123 です。"

        "公開する場合は ADMIN_PASSWORD を必ず変更してください。"

    )

    if st.button("← 通常ログインに戻る", use_container_width=True):

        go("login")

# =========================

# 管理者画面

# =========================

elif st.session_state.page == "admin":

    if not st.session_state.admin_authenticated:

        go("admin_login")

    st.markdown("<h1>お問い合わせ管理</h1>", unsafe_allow_html=True)

    top1, top2 = st.columns([3, 1])

    with top1:

        st.caption("SQLiteデータベースに保存されたお問い合わせを管理します。")

    with top2:

        if st.button("ログアウト", use_container_width=True):

            st.session_state.admin_authenticated = False

            go("login")

    search_col, status_col = st.columns([2, 1])

    with search_col:

        search_text = st.text_input(

            "検索",

            placeholder="名前・メール・電話・住所・内容・IDなど",

        )

    with status_col:

        status_filter = st.selectbox(

            "対応状況",

            ["すべて", "未対応", "対応済み"],

        )

    all_rows = fetch_contacts()

    rows = fetch_contacts(search_text, status_filter)

    pending_count = sum(1 for row in all_rows if row.get("status") == "未対応")

    completed_count = sum(1 for row in all_rows if row.get("status") == "対応済み")

    m1, m2, m3 = st.columns(3)

    m1.metric("全件", len(all_rows))

    m2.metric("未対応", pending_count)

    m3.metric("対応済み", completed_count)

    st.markdown("### データベース")

    db_path = get_db_path()

    st.caption(f"保存先: {db_path}")

    if os.path.exists(db_path):

        with open(db_path, "rb") as db_file:

            db_bytes = db_file.read()

        st.download_button(

            "💾 contact.db を保存",

            data=db_bytes,

            file_name="contact.db",

            mime="application/octet-stream",

            use_container_width=True,

        )

    st.markdown("### 問い合わせ一覧")

    if rows:

        display_rows = []

        for row in rows:

            display_rows.append(

                {

                    "ID": row.get("id"),

                    "送信日時": row.get("created_at"),

                    "氏名": f"{row.get('last_name', '')} {row.get('first_name', '')}".strip(),

                    "メール": row.get("email"),

                    "種類": row.get("inquiry_type"),

                    "対応状況": row.get("status"),

                    "内容": row.get("message"),

                }

            )

        st.dataframe(

            display_rows,

            use_container_width=True,

            hide_index=True,

        )

        st.download_button(

            "⬇️ 現在の一覧をCSV出力",

            data=contacts_to_csv(rows),

            file_name="contact_submissions.csv",

            mime="text/csv",

            use_container_width=True,

        )

        st.divider()

        st.markdown("### 選択した問い合わせを操作")

        row_by_id = {int(row["id"]): row for row in rows}

        selected_id = st.selectbox(

            "問い合わせIDを選択",

            options=list(row_by_id.keys()),

            format_func=lambda contact_id: (

                f"ID {contact_id} | "

                f"{row_by_id[contact_id].get('last_name', '')} "

                f"{row_by_id[contact_id].get('first_name', '')} | "

                f"{row_by_id[contact_id].get('status', '')}"

            ),

        )

        selected = row_by_id[int(selected_id)]

        with st.expander("問い合わせ詳細", expanded=True):

            st.write(f"**氏名:** {selected.get('last_name', '')} {selected.get('first_name', '')}")

            st.write(f"**性別:** {selected.get('gender', '')}")

            st.write(f"**メール:** {selected.get('email', '')}")

            st.write(f"**電話番号:** {selected.get('phone', '')}")

            st.write(f"**住所:** {selected.get('address', '')}")

            st.write(f"**建物名:** {selected.get('building', '') or '―'}")

            st.write(f"**種類:** {selected.get('inquiry_type', '')}")

            st.write(f"**タグ:** {selected.get('tags', '') or '―'}")

            st.write(f"**送信日時:** {selected.get('created_at', '')}")

            st.write("**お問い合わせ内容:**")

            st.write(selected.get("message", ""))

        current_status = selected.get("status", "未対応")

        new_status = st.radio(

            "対応状況を変更",

            ["未対応", "対応済み"],

            index=0 if current_status == "未対応" else 1,

            horizontal=True,

            key=f"status_{selected_id}",

        )

        if st.button("対応状況を保存", use_container_width=True):

            update_contact_status(selected_id, new_status)

            st.success(f"ID {selected_id} を「{new_status}」に変更しました。")

            st.rerun()

        st.markdown("#### 削除")

        delete_confirm = st.checkbox(

            f"ID {selected_id} を削除することを確認しました",

            key=f"delete_confirm_{selected_id}",

        )

        if st.button(

            "🗑️ この問い合わせを削除",

            use_container_width=True,

            disabled=not delete_confirm,

        ):

            delete_contact(selected_id)

            st.success(f"ID {selected_id} を削除しました。")

            st.rerun()

    else:

        st.info("条件に一致するお問い合わせはありません。")

        st.download_button(

            "⬇️ CSV出力（0件）",

            data=contacts_to_csv([]),

            file_name="contact_submissions.csv",

            mime="text/csv",

            use_container_width=True,

            disabled=True,

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

            save_contact_db(d)

            go("complete")

    with right:

        if st.button("修正", use_container_width=True):

            go("contact")

# =========================

# 4. 完了画面

# =========================

elif st.session_state.page == "complete":

    st.markdown(

        """<div class="thanks-wrap">

<div class="thanks-bg">Thank you</div>

<div class="thanks-message">お問い合わせありがとうございました</div>

</div>""",

        unsafe_allow_html=True,

    )

    saved_id = st.session_state.get("saved_contact_id")

    if saved_id:

        st.success(f"お問い合わせをデータベースに保存しました（ID: {saved_id}）")

    if st.button("HOME", use_container_width=True):

        st.session_state.login_data = {}

        st.session_state.contact_data = {}

        go("login")