"""Style, proofreading and duplicate review without implicit database writes."""
from __future__ import annotations

import copy
import hashlib
import json
import sqlite3

import streamlit as st

from miyabi import ai_client
from miyabi.ai_controls import render_ai_settings, render_generation
from miyabi.database import FIELDS, GENRES, empty_article
from miyabi.export import article_markdown
from miyabi.review import STYLE_MODES, ReviewError, accept_issue, local_duplicates, patched_body

STYLE_PAGE = "みやび文体変換"
PROOF_PAGE = "AI文章校正"
DUPLICATE_PAGE = "重複チェック"


def review_space(store, target):
    spaces = st.session_state.setdefault("review_spaces", {})
    if target not in spaces:
        source, version = empty_article(), None
        if target in st.session_state.drafts:
            draft = st.session_state.drafts[target]
            source.update(draft["values"])
            version = draft["version"]
        elif target != "new":
            article = store.get(int(target))
            if article:
                source.update({key: article[key] for key in FIELDS})
                version = article["updated_at"]
        spaces[target] = {
            "source": source, "version": version,
            "values": {key: source[key] for key in ("body", "title", "genre", "audience", "outline")} | {"style_mode": STYLE_MODES[0], "style_candidate": ""},
            "results": {}, "history": [], "references": {}, "reference_ids": [],
        }
    return spaces[target]


def set_body(target, body):
    st.session_state.review_spaces[target]["values"]["body"] = body
    st.session_state[f"review_{target}_body"] = body


def reload_review(target):
    st.session_state.review_spaces.pop(target, None)
    for key in list(st.session_state):
        if key.startswith(f"review_{target}_") or key.startswith(f"consent_review_{target}_"):
            st.session_state.pop(key, None)


def mutation(target, after, proof_before=None):
    space = st.session_state.review_spaces[target]
    entry = {"before": space["values"]["body"], "after": after, "proof_before": proof_before}
    space["history"].append(entry)
    set_body(target, after)
    space["message"] = "作業中の本文へ採用しました。記事への保存はまだ行っていません。"


def adopt_style(target):
    space = st.session_state.review_spaces[target]
    result = space["results"]["style"]
    try:
        current = ai_client.prepare_request("style", space["values"], st.session_state["ai_preferences"]["model"])
    except ai_client.GenerationError:
        current = None
    if current is None or current.fingerprint != result["fingerprint"]:
        space["error"] = "変換後に原文や条件が変わりました。現在の文章でもう一度変換してください。"
        return
    candidate = space["values"]["style_candidate"]
    if not candidate.strip():
        space["error"] = "採用する文章が空欄です。"
        return
    mutation(target, candidate)


def adopt_issue(target, index):
    space = st.session_state.review_spaces[target]
    result = space["results"]["proof"]
    if not proof_is_fresh(space, st.session_state["ai_preferences"]["model"]):
        space["error"] = "校正後に本文や条件が変わりました。現在の本文で再校正してください。"
        return
    try:
        after, accepted = accept_issue(result["source"], space["values"]["body"],
                                       result["data"]["issues"], result["accepted"], index)
    except ReviewError as exc:
        space["error"] = str(exc)
        return
    previous = {"generation": result["generation"], "accepted": list(result["accepted"])}
    mutation(target, after, previous)
    result["accepted"] = accepted


def undo(target):
    space = st.session_state.review_spaces[target]
    if not space["history"]:
        return
    entry = space["history"][-1]
    if space["values"]["body"] != entry["after"]:
        space["error"] = "採用後に本文を手動編集しています。手動編集を消さないため元に戻せません。必要な内容を退避して手動で修正してください。"
        return
    space["history"].pop()
    set_body(target, entry["before"])
    proof = space["results"].get("proof")
    previous = entry["proof_before"]
    if previous and proof and proof["generation"] == previous["generation"]:
        proof["accepted"] = previous["accepted"]
    space["message"] = "直前の採用を元に戻しました。保存済みの記事は変更していません。"


def apply_review(store, target):
    space = st.session_state.review_spaces[target]
    try:
        if target != "new" and store.get(int(target)) is None:
            raise ReviewError("反映先の記事が削除されています。本文を退避して別の記事へ移してください。")
        draft = st.session_state.drafts.get(target)
        if draft:
            expected = space.get("last_applied_body", space["source"]["body"])
            if draft["values"]["body"] != expected:
                raise ReviewError("編集画面の本文が作業開始後に変わっています。両方を退避して確認し、必要なら編集内容を読み込み直してください。")
        else:
            draft = {"values": copy.deepcopy(space["source"]), "version": space["version"], "dirty": False}
            st.session_state.drafts[target] = draft
        draft["values"]["body"] = space["values"]["body"]
        draft["dirty"] = True
        space["last_applied_body"] = space["values"]["body"]
        st.session_state.pop(f"edit_{target}_body", None)
        st.session_state.editor_id = None if target == "new" else int(target)
        st.session_state.page = "記事を書く・編集する"
        st.session_state.flash = "本文だけを編集欄へ反映しました。内容を確認して「記事を保存」を押してください。"
    except ReviewError as exc:
        space["error"] = str(exc)
    except (sqlite3.Error, OSError):
        space["error"] = "反映先の記事を開けませんでした。作業内容は残しています。保存先を確認してください。"


def signature(body, articles, target):
    rows = [(a["id"], a["updated_at"]) for a in articles if str(a["id"]) != target]
    return hashlib.sha256(json.dumps([body, rows], ensure_ascii=False).encode()).hexdigest()


def proof_is_fresh(space, model):
    result = space["results"].get("proof")
    if result is None:
        return False
    try:
        request = ai_client.prepare_request("proof", space["values"] | {"body": result["source"]}, model)
        return request.fingerprint == result["fingerprint"] and space["values"]["body"] == patched_body(
            result["source"], result["data"]["issues"], result["accepted"])
    except (ReviewError, ai_client.GenerationError):
        return False


def reset_reference(target, article):
    ref = st.session_state.review_spaces[target]["references"][str(article["id"])]
    ref.update(excerpt=article["body"][:3000], version=article["updated_at"])
    st.session_state[f"review_{target}_reference_{article['id']}"] = ref["excerpt"]


def render_review(store, kind):
    page = {"style": STYLE_PAGE, "proof": PROOF_PAGE, "duplicate": DUPLICATE_PAGE}[kind]
    st.header(page)
    articles = store.list()
    labels = {"new": "新しい文章・未保存の記事"} | {str(a["id"]): f'{a["title"]}（ID {a["id"]}）' for a in articles}
    for key in st.session_state.get("review_spaces", {}):
        if key not in labels:
            labels[key] = f"元記事が見つからない作業中の本文（ID {key}）"
    st.session_state.setdefault("review_target", st.session_state.get("review_selected_target", "new"))
    if st.session_state.review_target not in labels:
        st.session_state.review_target = "new"
    target = st.selectbox("対象の記事", list(labels), format_func=labels.get, key="review_target")
    st.session_state.review_selected_target = target
    space = review_space(store, target)
    v = space["values"]
    st.info("作業中の本文は3つの校正画面で共有し、画面移動中も保持します。終了・再読み込みの前に退避するか、「本文を記事編集へ反映」→「記事を保存」を押してください。採用だけでは保存済みの記事は変わりません。")

    def remember(name, widget):
        v[name] = st.session_state[widget]

    def field(name, label, area=False, **kwargs):
        key = f"review_{target}_{name}"
        st.session_state.setdefault(key, v[name])
        options = dict(key=key, on_change=remember, args=(name, key))
        return st.text_area(label, **options, **kwargs) if area else st.text_input(label, **options, **kwargs)

    with st.expander("タイトル・読者などの確認用情報"):
        field("title", "確認用タイトル")
        field("audience", "確認用の想定読者")
        genre_key = f"review_{target}_genre"
        st.session_state.setdefault(genre_key, v["genre"])
        st.selectbox("確認用ジャンル", GENRES, key=genre_key, on_change=remember, args=("genre", genre_key))
        field("outline", "確認用の記事構成", area=True, height=100)
        st.caption("記事に反映するのは本文だけです。この確認用情報や記事の公開情報・備考は書き換えません。")
    field("body", "確認・編集する本文", area=True, height=280)
    st.caption(f'本文 {len(v["body"]):,}文字')
    with st.expander("編集画面の内容を読み込み直す"):
        st.caption("作業中の本文・候補・採用履歴を破棄して、現在の編集下書き（なければ保存済み記事）を読み込みます。必要な内容は先にダウンロードしてください。")
        reload_ok = st.checkbox("作業内容を破棄して読み込み直します", key=f"review_{target}_reload_ok")
        st.button("編集内容を読み込み直す", disabled=not reload_ok, on_click=reload_review, args=(target,))
    if "error" in space:
        st.error(space.pop("error"))
    if "message" in space:
        st.success(space.pop("message"))
    st.button("元に戻す", disabled=not space["history"], on_click=undo, args=(target,))
    if v["genre"] in ("健康と美容", "お金とこれからの生活"):
        st.warning("健康・美容・お金の効果や結果を断定せず、公開前に信頼できる根拠を確認してください。AIは外部情報を調査していません。")

    if kind == "duplicate":
        render_local(space, v, articles, target)
        st.subheader("選んだ過去記事とAIで内容を比較（任意・従量課金）")
    prefs = render_ai_settings()
    if kind == "style":
        style_key = f"review_{target}_style_mode"
        st.session_state.setdefault(style_key, v["style_mode"])
        st.selectbox("みやび文体のモード", STYLE_MODES, key=style_key, on_change=remember, args=("style_mode", style_key))
    request_values = dict(v)
    if kind == "duplicate":
        request_values["references"] = render_references(space, articles, target)
    request = None
    try:
        request = ai_client.prepare_request(kind, request_values, prefs["model"])
    except ai_client.GenerationError as exc:
        st.caption(str(exc))
    action = {"style": "みやび文体に変換", "proof": "10項目でAI校正する", "duplicate": "選んだ記事とAI比較する"}[kind]
    result = render_generation(request, space, f"review_{target}_{kind}", action)
    if result is not None:
        space["generation"] = space.get("generation", 0) + 1
        space["results"][kind] = {"source": v["body"], "data": result, "fingerprint": request.fingerprint,
                                  "accepted": [], "generation": space["generation"]}
        if kind == "style":
            v["style_candidate"] = result["converted"]
            st.session_state[f"review_{target}_style_candidate"] = result["converted"]
        st.rerun()
    saved_result = space["results"].get(kind)
    if saved_result:
        st.subheader("確認結果")
        st.caption("外部情報：未検証。指摘なしでも、誤りや重複がないことを保証するものではありません。")
        st.download_button("確認結果をJSONで退避", json.dumps(saved_result["data"], ensure_ascii=False, indent=2).encode(),
                           file_name=f"miyabi_{kind}_review.json", mime="application/json", key=f"review_{target}_{kind}_download")
        fresh = proof_is_fresh(space, prefs["model"]) if kind == "proof" else request is not None and request.fingerprint == saved_result["fingerprint"]
        if not fresh:
            st.warning("確認後に本文や条件が変わっています。以前の結果を残していますが、現在の本文で再実行するまで採用できません。")
        if kind == "style":
            left, right = st.columns(2)
            left.text_area("変更前（生成時の原文）", value=saved_result["source"], disabled=True, height=300,
                           key=f'review_{target}_before_{saved_result["generation"]}')
            with right:
                field("style_candidate", "変更後（手動編集可）", area=True, height=300)
            for note in saved_result["data"]["notes"]:
                st.write(note)
            st.caption("意味・事実・数字・ご自身の体験が変わっていないか確認してから採用してください。")
            st.button("修正を採用", disabled=not fresh or not v["style_candidate"].strip(), on_click=adopt_style, args=(target,))
        elif kind == "proof":
            render_proof(space, saved_result, target, fresh)
        else:
            for finding in saved_result["data"]["findings"]:
                with st.container(border=True):
                    st.write(f'比較先の記事ID：{finding["article_id"]}')
                    st.write("今回の本文：" + finding["current_quote"])
                    st.write("過去記事の引用：" + finding["past_quote"])
                    st.write("重複の可能性：" + finding["reason"])
                    st.write("切り口の提案：" + finding["suggestion"])
            if not saved_result["data"]["findings"]:
                st.info("指定した抜粋の範囲で、AIから重複の指摘はありませんでした。記事全文やインターネット全体を確認した結果ではありません。")

    st.divider()
    st.subheader("本文の退避・記事保存へ")
    st.download_button("作業中の本文をMarkdownで退避", article_markdown({"title": v["title"], "body": v["body"]}),
                       file_name="miyabi_review_draft.md", mime="text/markdown", key=f"review_{target}_draft_download")
    confirm = st.checkbox("選択した記事の編集欄の本文に反映します", key=f"review_{target}_apply_confirm")
    st.button("本文を記事編集へ反映", disabled=not confirm, on_click=apply_review, args=(store, target), type="primary")


def render_proof(space, result, target, fresh):
    issues = result["data"]["issues"]
    if not issues:
        st.info("10項目の確認でAIから指摘はありませんでした。公開前のご自身による確認もお願いします。")
    for index, issue in enumerate(issues):
        with st.container(border=True):
            st.subheader(f'{index + 1}. {issue["category"]}')
            st.write("修正前：" + issue["before"])
            st.write("修正候補：" + (issue["after"] or "（削除）"))
            st.write("理由：" + issue["reason"])
            st.caption(f'同じ引用が現れる順番：{issue["occurrence"]}番目 ｜ 外部情報：未検証')
            unavailable = None
            if index in result["accepted"]:
                st.success("採用済み")
            elif fresh:
                try:
                    accept_issue(result["source"], space["values"]["body"], issues, result["accepted"], index)
                    if issue["before"] == issue["after"]:
                        unavailable = "修正前後が同じため、確認だけの指摘です。"
                except ReviewError as exc:
                    unavailable = str(exc)
            if unavailable:
                st.info(unavailable)
            st.button("この修正を採用", key=f"review_{target}_issue_{result['generation']}_{index}",
                      disabled=not fresh or index in result["accepted"] or bool(unavailable), on_click=adopt_issue, args=(target, index))


def render_local(space, v, articles, target):
    st.subheader("ローカル重複チェック（API不要・無料）")
    st.caption("本文の文字列を比較します。空白・句読点・全角半角を整えた文字3個の並びの共通度を目安にします。意味が同じ別表現や盗用を判定する機能ではありません。対象記事自身は比較から除外します。")
    threshold = st.slider("似ている箇所を表示する目安（%）", min_value=40, max_value=100, value=65, step=5,
                          key=f"review_{target}_threshold")
    current_signature = signature(v["body"], articles, target) + str(threshold)
    if st.button("ローカルで重複を確認", key=f"review_{target}_local_run"):
        try:
            with st.spinner("保存済み記事との文字列の重なりを確認しています。"):
                data = local_duplicates(v["body"], articles, None if target == "new" else target, threshold / 100)
        except ReviewError as exc:
            st.error(str(exc))
        else:
            space["local"] = {"signature": current_signature, "data": data}
    local = space.get("local")
    if not local:
        return
    if local["signature"] != current_signature:
        st.warning("本文・比較記事・しきい値が変わっています。表示は前回の結果です。もう一度確認してください。")
    data = local["data"]
    st.caption(f'本文内：{data["units_checked"]}/{data["units_total"]}文を比較 ／ 保存済み記事：{data["checked_articles"]}件を比較')
    if data["units_checked"] < data["units_total"] or data["limited_articles"] or data["skipped_articles"]:
        st.warning(f'本文内・過去記事の抜粋比較は先頭300文まで。10万文字超で除外した記事ID：{data["skipped_articles"]}。抜粋を先頭300文に制限した記事ID：{data["limited_articles"]}。全体の文字列共通度は10万文字以内の記事全文で比較しています。')
    st.write(f'記事内の候補：{data["internal_total"]}組（上位20組まで表示）')
    for item in data["internal"]:
        with st.container(border=True):
            st.caption(f'{item["first"]}番目と{item["second"]}番目の文 ｜ {item["kind"]} ｜ 共通度の目安 {item["score"]:.0%}')
            st.write(item["before"])
            st.write(item["similar"])
    st.write(f'過去記事との候補：{data["past_total"]}件（上位20件まで表示）')
    for item in data["past"]:
        with st.container(border=True):
            st.write(f'{item["title"]}（ID {item["id"]}）')
            st.caption(f'最も共通する箇所の目安：{item["score"]:.0%}。記事全体がこの割合で重複するという意味ではありません。')
            st.write("今回の箇所：" + item["current_excerpt"])
            st.write("過去記事の抜粋：" + item["excerpt"])
    if not data["internal"] and not data["past"]:
        st.info("今回の条件と確認範囲では文字列の重なりの候補が見つかりませんでした。意味の重複がないことを保証しません。")


def render_references(space, articles, target):
    candidates = {str(a["id"]): a for a in articles if str(a["id"]) != target and a["body"].strip()}
    ref_key = f"review_{target}_reference_ids"
    valid = [key for key in space["reference_ids"] if key in candidates]
    st.session_state.setdefault(ref_key, valid)
    if any(key not in candidates for key in st.session_state[ref_key]):
        st.session_state[ref_key] = valid
    def selection_changed():
        space["reference_ids"] = st.session_state[ref_key]
    selected = st.multiselect("AI比較する過去記事（最大5件）", list(candidates), key=ref_key, max_selections=5,
                              format_func=lambda key: f'{candidates[key]["title"]}（ID {key}）', on_change=selection_changed)
    st.caption("選んだ記事の抜粋だけを送ります。最初は各記事の先頭3000文字を表示します。比較したい箇所へ編集してから送信内容を確認してください。全文を自動で送信することはありません。")
    refs = []
    for key in selected:
        article = candidates[key]
        ref = space["references"].setdefault(key, {"excerpt": article["body"][:3000], "version": article["updated_at"]})
        widget = f"review_{target}_reference_{key}"
        st.session_state.setdefault(widget, ref["excerpt"])
        def changed(k=key, w=widget):
            space["references"][k]["excerpt"] = st.session_state[w]
        st.text_area(f'{article["title"]}：送信する抜粋（3000文字以内）', key=widget, on_change=changed, height=160)
        if ref["version"] != article["updated_at"]:
            st.warning("この抜粋を用意した後に元の記事が更新されました。必要なら最新の本文から読み直してください。")
        st.button("この抜粋を最新本文から読み直す", key=f"review_{target}_refresh_{key}", on_click=reset_reference, args=(target, article))
        refs.append({"article_id": key, "title": article["title"], "excerpt": ref["excerpt"]})
    return refs


def render_style(store):
    render_review(store, "style")


def render_proofreading(store):
    render_review(store, "proof")


def render_duplicates(store):
    render_review(store, "duplicate")
