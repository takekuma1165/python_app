"""Editable, durable note/Threads preparation with no automatic posting."""
import copy
import json
import sqlite3
import streamlit as st
from miyabi import ai_client
from miyabi.ai_controls import render_ai_settings, render_generation
from miyabi.database import FIELDS
from miyabi.export import article_markdown, article_text, download_name
from miyabi.publication import PACK_FIELDS, empty_pack, validate_pack


LABELS = {"title": "最終タイトル", "body": "完成本文", "hashtags": "note用ハッシュタグ（推奨5〜8個）",
          "introduction": "記事の紹介文", "thread_1": "Threads告知文 1", "thread_2": "Threads告知文 2",
          "thread_3": "Threads告知文 3", "cover": "アイキャッチ画像に入れる短い言葉", "closing": "コメントを促す締めの文章"}


def publication_space(store, article):
    spaces = st.session_state.setdefault("publication_spaces", {})
    key = str(article["id"])
    if key not in spaces:
        saved = store.publication(article["id"])
        spaces[key] = {"values": copy.deepcopy(saved["data"]) if saved else empty_pack(article),
                       "version": saved["updated_at"] if saved else None,
                       "source_version": saved["source_updated_at"] if saved else article["updated_at"],
                       "source": dict(article), "dirty": False, "history": []}
    return spaces[key]


def refresh_article(key, article):
    space = st.session_state.publication_spaces[key]
    space["source"] = dict(article); space["source_version"] = article["updated_at"]
    for field in ("title", "body", "hashtags"):
        space["values"][field] = article[field]
        st.session_state[f"pub_{key}_{field}"] = article[field]
    space["dirty"] = True
    space.pop("result", None)


def undo_publication(key):
    space = st.session_state.publication_spaces[key]
    if space["history"]:
        previous = space["history"].pop()
        for field in PACK_FIELDS:
            space["values"][field] = previous[field]
            st.session_state[f"pub_{key}_{field}"] = previous[field]
        space["dirty"] = True
        space.pop("result", None)


def append_closing(key):
    space = st.session_state.publication_spaces[key]
    v = space["values"]
    if v["closing"].strip() and not v["body"].rstrip().endswith(v["closing"].strip()):
        space["history"].append(copy.deepcopy(v))
        v["body"] = v["body"].rstrip() + "\n\n" + v["closing"].strip()
        st.session_state[f"pub_{key}_body"] = v["body"]
        space["dirty"] = True


def apply_to_article(store, key):
    space = st.session_state.publication_spaces[key]
    try:
        if store.get(int(key)) is None:
            raise ValueError("元の記事が削除されました。投稿準備を退避してください。")
        v = validate_pack(space["values"])
        draft = st.session_state.drafts.get(key)
        if draft:
            original = space.get("last_applied", {f: space["source"][f] for f in ("title", "body", "hashtags")})
            if any(draft["values"][f] != original[f] for f in original):
                raise ValueError("編集画面に別の変更があります。両方を退避して確認してください。")
        else:
            draft = {"values": {f: space["source"][f] for f in FIELDS}, "version": space["source_version"], "dirty": False}
            st.session_state.drafts[key] = draft
        applied = {f: v[f] for f in ("title", "body", "hashtags")}
        draft["values"].update(applied); draft["dirty"] = True
        space["last_applied"] = applied
        for field in applied:
            st.session_state.pop(f"edit_{key}_{field}", None)
        st.session_state.editor_id = int(key); st.session_state.page = "記事を書く・編集する"
        st.session_state.flash = "最終タイトル・本文・タグを編集欄へ反映しました。「記事を保存」で確定してください。"
    except (ValueError, sqlite3.Error, OSError) as exc:
        space["error"] = str(exc) if isinstance(exc, ValueError) else "記事へ反映できませんでした。入力は保持しています。"


def render_publication(store):
    st.header("出力・投稿準備")
    st.caption("noteへの投稿は手動です。タイトル・本文と、紹介文・Threads告知をまとめて準備できます。")
    articles = store.list()
    if not articles:
        st.info("まず記事を作成・保存してください。")
        return
    lookup = {str(a["id"]): a for a in articles}
    st.session_state.setdefault("publication_target", st.session_state.get("publication_selected", next(iter(lookup))))
    if st.session_state.publication_target not in lookup:
        st.session_state.publication_target = next(iter(lookup))
    key = st.selectbox("出力する記事", list(lookup), format_func=lambda i: f'{lookup[i]["title"]}（ID {i}）', key="publication_target")
    st.session_state.publication_selected = key
    article = lookup[key]; space = publication_space(store, article); v = space["values"]
    if space["source_version"] != article["updated_at"]:
        st.warning("投稿準備の元になった記事が更新されています。必要な投稿準備を退避してから、記事の最新内容を取り込んでください。")
    if st.session_state.drafts.get(key, {}).get("dirty"):
        st.warning("編集画面に未保存の変更があります。投稿準備は保存済みの記事を元にしています。")
    with st.expander("記事の最新内容を取り込む"):
        confirmed = st.checkbox("投稿準備のタイトル・本文・タグを最新記事で置き換えます", key=f"pub_{key}_refresh_confirm")
        st.button("最新記事のタイトル・本文・タグを取り込む", disabled=not confirmed, on_click=refresh_article, args=(key, article))
    def changed(field, widget):
        v[field] = st.session_state[widget]; space["dirty"] = True
    for field in PACK_FIELDS:
        widget = f"pub_{key}_{field}"; st.session_state.setdefault(widget, v[field])
        options = dict(key=widget, on_change=changed, args=(field, widget))
        if field in ("title", "cover"):
            st.text_input(LABELS[field], **options)
        else:
            st.text_area(LABELS[field], height=260 if field == "body" else 90, **options)
        if field.startswith("thread_"):
            st.caption(f'{len(v[field])}/500文字')
    st.button("締めの文章を本文の末尾へ追加", disabled=not v["closing"].strip(), on_click=append_closing, args=(key,))
    st.button("前の投稿準備に戻す", disabled=not space["history"], on_click=undo_publication, args=(key,))
    if "error" in space:
        st.error(space.pop("error"))
    if space["dirty"]:
        st.warning("投稿準備に未保存の変更があります。記事本体とは別に保存してください。")
    if st.button("投稿準備を保存", type="primary"):
        try:
            space["version"] = store.save_publication(int(key), v, space["source_version"], space["version"])
        except (ValueError, sqlite3.Error, OSError) as exc:
            st.error(str(exc) if isinstance(exc, ValueError) else "投稿準備を保存できませんでした。入力は保持しています。")
        else:
            space["dirty"] = False
            st.success("投稿準備を保存しました。記事本体は変更していません。")
    prefs = render_ai_settings()
    st.subheader("AIで告知文・タグを作る（任意）")
    st.caption("現在の最終タイトル・完成本文だけを素材に、タグ5〜8個、紹介文、Threads告知3案、画像用の短い言葉、締めを作ります。生成すると告知欄の候補を置き換えます。「前の投稿準備に戻す」で取り消せます。")
    request = None
    try:
        request = ai_client.prepare_request("publication", {"title": v["title"], "body": v["body"], "genre": article["genre"],
                                                           "audience": article["audience"], "tone": prefs.get("tone", "")}, prefs["model"])
    except ai_client.GenerationError as exc:
        st.caption(str(exc))
    generated = render_generation(request, space, f"pub_{key}", "投稿準備の候補を生成")
    if generated is not None:
        space["history"].append(copy.deepcopy(v))
        updates = {"hashtags": " ".join(generated["hashtags"]), "introduction": generated["introduction"],
                   "cover": generated["cover"], "closing": generated["closing"],
                   **{f"thread_{i}": text for i, text in enumerate(generated["threads"], 1)}}
        v.update(updates)
        for field in updates:
            st.session_state.pop(f"pub_{key}_{field}", None)
        space["result"] = {"fingerprint": request.fingerprint}
        space["dirty"] = True
        st.rerun()
    st.caption("AIの告知は外部情報未検証です。体験・効果・公開予定などが本文と一致するか確認してください。")
    if space.get("result") and (request is None or space["result"]["fingerprint"] != request.fingerprint):
        st.warning("AI生成後にタイトル・本文・モデル等が変わっています。告知文が合っているか見直してください。")
    st.subheader("完成記事をダウンロード・コピー")
    st.caption("いま表示している最終タイトル・本文・タグを出力します。備考や告知文は記事ファイルに含めません。")
    c1, c2 = st.columns(2)
    c1.download_button("Markdownをダウンロード", article_markdown(v).encode(), file_name=download_name(v["title"], "md"), mime="text/markdown")
    c2.download_button("テキストをダウンロード", article_text(v).encode("utf-8-sig"), file_name=download_name(v["title"], "txt"), mime="text/plain")
    st.text_area("コピー用テキスト（変更は保存されません）", article_text(v), height=230,
                 key=f'pub_copy_{key}_{hash(article_text(v))}')
    with st.expander("告知文をコピー"):
        for field in ("introduction", "thread_1", "thread_2", "thread_3", "cover", "closing"):
            st.caption(LABELS[field]); st.code(v[field], language=None)
    if space["version"]:
        st.download_button("投稿準備一式をJSONで退避", json.dumps(v, ensure_ascii=False, indent=2).encode(),
                           file_name="miyabi_publication.json", mime="application/json")
    confirmed = st.checkbox("最終タイトル・本文・タグを記事の編集欄へ反映します", key=f"pub_{key}_apply_confirm")
    st.button("完成記事を編集欄へ反映", disabled=not confirmed, on_click=apply_to_article, args=(store, key))
