"""Japanese, offline-first Streamlit interface for article editing and AI-assisted writing."""
from __future__ import annotations

import sqlite3
import streamlit as st

from miyabi.database import ArticleStore, FIELDS, GENRES, STATUSES, empty_article
from miyabi.export import article_markdown, article_text, download_name
from miyabi.ai_client import api_key_configured
from miyabi.ai_ui import AI_PAGE, render_ai
from miyabi.review_ui import STYLE_PAGE, PROOF_PAGE, DUPLICATE_PAGE, render_style, render_proofreading, render_duplicates

PAGES = ("ホーム", "記事を書く・編集する", "記事一覧", "出力・投稿準備", "このアプリについて", AI_PAGE, STYLE_PAGE, PROOF_PAGE, DUPLICATE_PAGE)
LABELS = {
    "title": "タイトル（必須）", "genre": "ジャンル", "audience": "対象読者",
    "keyword": "メインキーワード", "search_intent": "検索意図・読者の悩み",
    "outline": "記事構成", "body": "本文", "hashtags": "ハッシュタグ",
    "status": "記事ステータス", "published_on": "公開日（YYYY-MM-DD・任意）",
    "note_url": "note記事URL（任意）", "notes": "備考・自分の経験メモ（出力されません）",
}


def go(page: str, article_id: int | None = None):
    st.session_state.page = page
    if article_id is not None:
        st.session_state.editor_id = article_id


def new_article():
    st.session_state.editor_id = None
    st.session_state.page = PAGES[1]


def draft_key(article_id):
    return str(article_id) if article_id is not None else "new"


def remember(key: str, field: str, widget_key: str):
    draft = st.session_state.drafts[key]
    draft["values"][field] = st.session_state[widget_key]
    draft["dirty"] = True


def notify_error(exc):
    if isinstance(exc, ValueError):
        st.error(str(exc))
    else:
        st.error("保存処理を完了できませんでした。入力内容はこの画面に残っています。出力ボタンで文章を退避し、保存先の権限・空き容量を確認して再度お試しください。")


def export_buttons(article: dict, key: str):
    left, right = st.columns(2)
    left.download_button("Markdownをダウンロード", article_markdown(article).encode("utf-8"),
                         file_name=download_name(article.get("title", ""), "md"),
                         mime="text/markdown", key=f"md_{key}", use_container_width=True)
    right.download_button("テキストをダウンロード", article_text(article).encode("utf-8-sig"),
                          file_name=download_name(article.get("title", ""), "txt"),
                          mime="text/plain", key=f"txt_{key}", use_container_width=True)


def render_home(store):
    st.header("あなたの言葉を、少しずつ記事に。")
    st.write("自分の経験や思いを大切にしながら、企画から公開準備まで整えていきましょう。")
    articles = store.list()
    cols = st.columns(3)
    cols[0].metric("保存した記事", len(articles))
    cols[1].metric("作成中", sum(a["status"] not in ("完成", "公開済み") for a in articles))
    cols[2].metric("完成・公開済み", sum(a["status"] in ("完成", "公開済み") for a in articles))
    st.button("＋ 新しい記事を書く", on_click=new_article, type="primary")
    st.button("AIと記事を企画する", on_click=go, args=(AI_PAGE,))
    st.subheader("最近編集した記事")
    if not articles:
        st.info("まだ記事はありません。「新しい記事を書く」から、仮のタイトルとメモを保存してみましょう。")
    for a in articles[:5]:
        with st.container(border=True):
            st.write(a["title"])
            st.caption(f'{a["status"]} ｜ {a["genre"]} ｜ 更新 {a["updated_at"][:16].replace("T", " ")}')
            st.button("この記事を開く", key=f'home_{a["id"]}', on_click=go, args=(PAGES[1], a["id"]))


def render_editor(store):
    st.header("記事を書く・編集する")
    article_id = st.session_state.editor_id
    key = draft_key(article_id)
    drafts = st.session_state.drafts
    if key not in drafts:
        saved = store.get(article_id) if article_id is not None else None
        if article_id is not None and saved is None:
            st.warning("この記事は見つかりません。一覧から記事を選び直してください。")
            return
        drafts[key] = {"values": {f: saved[f] for f in FIELDS} if saved else empty_article(),
                       "version": saved["updated_at"] if saved else None, "dirty": False}
    draft = drafts[key]
    st.caption("新しい記事" if article_id is None else f"記事ID：{article_id}")
    st.info("入力は画面移動中も一時保持します。終了・再読み込みの前に「記事を保存」を押してください。ブラウザーを閉じた後の未保存入力は復元できません。")

    def field(name, kind="text", **kwargs):
        widget_key = f"edit_{key}_{name}"
        if widget_key not in st.session_state:
            st.session_state[widget_key] = draft["values"][name]
        common = dict(key=widget_key, on_change=remember, args=(key, name, widget_key))
        if kind == "select":
            return st.selectbox(LABELS[name], **common, **kwargs)
        if kind == "area":
            return st.text_area(LABELS[name], **common, **kwargs)
        return st.text_input(LABELS[name], **common, **kwargs)

    field("title")
    left, right = st.columns(2)
    with left:
        field("genre", "select", options=GENRES)
        field("audience")
        field("keyword")
    with right:
        field("status", "select", options=STATUSES)
        field("published_on", placeholder="例：2026-10-27")
        field("note_url", placeholder="https://note.com/…")
    field("search_intent", "area", height=90)
    field("outline", "area", height=140, placeholder="## はじめに\n## 伝えたいこと\n## まとめ")
    field("body", "area", height=360, placeholder="ここに本文を書きましょう。Markdownの見出しも使えます。")
    st.caption(f'本文：{len(draft["values"]["body"]):,}文字（空白・改行を含む）')
    field("hashtags", placeholder="#暮らし #自分らしく")
    field("notes", "area", height=120, placeholder="実際に経験したこと、試したこと、読者に伝えたいことなど。")
    if draft["dirty"]:
        st.warning("未保存の変更があります。")
    if st.button("記事を保存", type="primary", use_container_width=True):
        try:
            saved_id = store.save(draft["values"], article_id, draft["version"])
        except (sqlite3.Error, OSError, ValueError) as exc:
            notify_error(exc)
        else:
            drafts.pop(key, None)
            for name in FIELDS:
                st.session_state.pop(f"edit_{key}_{name}", None)
            st.session_state.editor_id = saved_id
            st.session_state.flash = "記事を保存しました。"
            st.rerun()
    def open_review(page):
        st.session_state.review_target = key
        st.session_state.page = page
    st.button("本文を校正・確認する", on_click=open_review, args=(PROOF_PAGE,))
    st.subheader("入力中の文章を出力")
    st.caption("未保存の内容も出力できます。備考と構成メモは含みません。")
    export_buttons(draft["values"], f"editor_{key}")
    with st.expander("本文プレビュー"):
        st.markdown(article_markdown(draft["values"]))


def render_list(store):
    st.header("記事一覧")
    st.button("＋ 新しい記事を書く", on_click=new_article, type="primary")
    c1, c2, c3 = st.columns([2, 1, 1])
    search = c1.text_input("記事を検索", placeholder="タイトル・本文・キーワード")
    status = c2.selectbox("ステータスで絞り込み", ("すべて", *STATUSES))
    order = c3.selectbox("並べ替え", ("更新が新しい順", "作成が新しい順", "作成が古い順", "タイトル順"))
    articles = store.list(search, status, order)
    st.caption(f"{len(articles)}件の記事")
    if not articles:
        st.info("該当する記事はありません。検索条件を変えるか、新しく記事を作成してください。")
    for a in articles:
        article_id = a["id"]
        with st.container(border=True):
            st.subheader(a["title"])
            st.caption(f'ID {article_id} ｜ {a["genre"]} ｜ {a["status"]}')
            st.caption(f'作成 {a["created_at"][:16].replace("T", " ")} ／ 更新 {a["updated_at"][:16].replace("T", " ")}（日本時間）')
            cols = st.columns(3)
            cols[0].button("編集", key=f"open_{article_id}", on_click=go, args=(PAGES[1], article_id), use_container_width=True)
            if cols[1].button("複製", key=f"copy_{article_id}", use_container_width=True):
                try:
                    copied = store.duplicate(article_id)
                    st.session_state.flash = "記事を複製しました。公開情報は引き継いでいません。"
                    st.session_state.next_page = (PAGES[1], copied)
                    st.rerun()
                except (sqlite3.Error, OSError, ValueError) as exc:
                    notify_error(exc)
            if cols[2].button("削除", key=f"delete_{article_id}", use_container_width=True):
                st.session_state.pending_delete = (article_id, a["updated_at"])
            if st.session_state.get("pending_delete", (None,))[0] == article_id:
                st.warning(f'「{a["title"]}」を削除します。この操作は取り消せません。')
                if st.checkbox("この記事を削除することを確認しました", key=f"confirm_{article_id}"):
                    if st.button("削除を確定する", key=f"final_delete_{article_id}"):
                        try:
                            store.delete(*st.session_state.pending_delete)
                        except (sqlite3.Error, OSError, ValueError) as exc:
                            notify_error(exc)
                        else:
                            st.session_state.drafts.pop(str(article_id), None)
                            # Forget stale widget values for the deleted article too.
                            for field in FIELDS:
                                st.session_state.pop(f"edit_{article_id}_{field}", None)
                            st.session_state.pending_delete = (None,)
                            st.session_state.flash = "記事を削除しました。"
                            st.rerun()
                if st.button("キャンセル", key=f"cancel_{article_id}"):
                    st.session_state.pending_delete = (None,)
                    st.rerun()


def render_export(store):
    st.header("出力・投稿準備")
    st.write("保存済みの記事をファイルにして、noteの編集画面へ手動で貼り付けられます。")
    articles = store.list()
    if not articles:
        st.info("まず記事を作成・保存してください。")
        return
    lookup = {a["id"]: a for a in articles}
    selected = st.selectbox("出力する記事", list(lookup), format_func=lambda i: f'{lookup[i]["title"]}（ID {i}）')
    a = lookup[selected]
    key = str(selected)
    if st.session_state.drafts.get(key, {}).get("dirty"):
        st.warning("この記事には未保存の編集があります。ここでは保存済みの内容を出力します。編集画面で保存するか、入力中の文章を出力してください。")
    st.caption("出力対象：タイトル・本文・ハッシュタグ。備考や検索意図は含みません。")
    export_buttons(a, "saved")
    st.text_area("コピー用テキスト（Ctrl+A → Ctrl+Cでコピー）", value=article_text(a), height=320, disabled=False, key=f'copy_text_{a["id"]}_{a["updated_at"]}')
    st.caption("コピー用欄の変更は記事へ保存されません。編集は「記事を書く・編集する」で行ってください。")
    with st.expander("Markdownプレビュー", expanded=True):
        st.markdown(article_markdown(a))
    st.info("noteへの自動投稿は行いません。AIによるハッシュタグ・紹介文・Threads告知文の生成は第4段階で追加予定です。")


def render_about(store):
    st.header("このアプリについて")
    st.write("みやび AIライティングスタジオ · 第3段階")
    st.write("記事の作成・編集・保存・検索・複製・削除と、Markdown／テキスト出力を利用できます。")
    st.caption(f"データ保存先：{store.path}")
    st.write("APIキー：" + ("設定あり（値は表示しません）" if api_key_configured() else "未設定。記事の手動編集・保存は利用できます。"))
    st.info("「AI記事づくり」でテーマ・タイトル・構成・本文の生成を利用できます。APIキー設定と送信内容・料金の確認後にのみOpenAIへ送信します。生成しなければAPI料金は発生しません。")
    st.write("文体変換・1件ずつ採用できるAI校正・重複チェックも利用できます。今後の追加予定：投稿準備支援、詳細ダッシュボード、設定・バックアップ画面。")
    st.write("保存済みデータの退避方法：アプリを停止した後、保存先フォルダー内の miyabi.sqlite3 を別の安全な場所へコピーしてください。復元時もアプリを停止し、現在のファイルを退避してから戻します。")


def render_app(store: ArticleStore):
    st.markdown('''<style>
    .stApp {background-color:#faf5ef;color:#423c38;}
    [data-testid="stSidebar"] {background-color:#efe4df;}
    [data-testid="stVerticalBlockBorderWrapper"] {background-color:#fffdfb;border-radius:14px;}
    h1,h2,h3 {color:#79545e;}
    .stApp, button, input, textarea {font-family:"Yu Gothic","Meiryo",sans-serif;}
    .stButton button {min-height:2.8rem;border-radius:9px;}
    .stButton button[kind="primary"] {background-color:#94616f;border-color:#94616f;color:white;}
    [data-testid="stMetricValue"] {color:#4b6b59;}
    </style>''', unsafe_allow_html=True)
    if "next_page" in st.session_state:
        go(*st.session_state.pop("next_page"))
    st.session_state.setdefault("drafts", {})
    st.session_state.setdefault("editor_id", None)
    st.session_state.setdefault("page", PAGES[0])
    with st.sidebar:
        st.title("みやび")
        st.caption("AIライティングスタジオ")
        page = st.radio("メニュー", PAGES, key="page")
        st.button("＋ 新しい記事", on_click=new_article, use_container_width=True)
        dirty = sum(d["dirty"] for d in st.session_state.drafts.values())
        if dirty:
            st.warning(f"未保存の下書き：{dirty}件")
            keys = [k for k, d in st.session_state.drafts.items() if d["dirty"]]
            for key in keys:
                title = st.session_state.drafts[key]["values"]["title"] or "無題の下書き"
                def resume(k=key):
                    st.session_state.editor_id = None if k == "new" else int(k)
                    st.session_state.page = PAGES[1]
                st.button(f"下書きに戻る：{title}", key=f"resume_{key}", on_click=resume)
        st.caption("第3段階 ｜ 執筆・文体・校正・重複確認")
    st.title("みやび AIライティングスタジオ")
    st.caption("みやびのnote ｜ 経験と思いを、あなたらしい言葉で。")
    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))
    renderers = dict(zip(PAGES, (render_home, render_editor, render_list, render_export, render_about, render_ai, render_style, render_proofreading, render_duplicates)))
    try:
        renderers[page](store)
    except (sqlite3.Error, OSError):
        st.error("データベースを読み書きできませんでした。入力中の下書きはセッション内に保持しています。保存先の権限・空き容量を確認してください。")
