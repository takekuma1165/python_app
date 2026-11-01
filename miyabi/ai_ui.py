"""Four-step AI workflow, with review before sending and explicit draft adoption."""
from __future__ import annotations

import copy
import json
import sqlite3

import streamlit as st

from miyabi import ai_client
from miyabi.ai_controls import render_ai_settings, render_generation
from miyabi.database import FIELDS, GENRES, empty_article
from miyabi.export import article_markdown

AI_PAGE = "AI記事づくり"
STEPS = ("① テーマ企画", "② SEOタイトル", "③ 記事構成", "④ 本文執筆")
DEFAULTS = {
    "genre": GENRES[0], "audience": "40代・50代・60代以上の女性", "problem": "", "message": "",
    "purpose": "共感", "keyword": "", "theme": "", "title": "", "search_intent": "",
    "outline": "", "body": "", "word_count": 2000, "revision": "", "outline_action": "新規・再生成",
    "mode": ai_client.MODES[0], "section": "", "existing_body": "", "memo": "",
    "experience": "", "experience_problem": "", "experience_thought": "", "experience_tried": "",
    "experience_message": "", "generated_outline": "", "generated_body": "",
}


def workspace(store, target):
    spaces = st.session_state.setdefault("ai_workspaces", {})
    if target not in spaces:
        source = empty_article()
        source["audience"] = st.session_state.get("saved_settings", {}).get("audience", source["audience"])
        version = None
        draft = st.session_state.drafts.get(target)
        if draft:
            source.update(draft["values"])
            version = draft["version"]
        elif target != "new":
            article = store.get(int(target))
            if article:
                source.update({k: article[k] for k in FIELDS})
                version = article["updated_at"]
        values = copy.deepcopy(DEFAULTS)
        values["word_count"] = st.session_state.get("saved_settings", {}).get("word_count", 2000)
        values.update({k: source[k] for k in ("genre", "audience", "keyword", "search_intent", "title", "outline", "body")})
        values["existing_body"] = source["body"]
        values["theme"] = source["title"]
        spaces[target] = {"values": values, "step": STEPS[0], "results": {},
                          "source": copy.deepcopy(source), "version": version}
    return spaces[target]


def set_value(target, name, value):
    st.session_state.ai_workspaces[target]["values"][name] = value
    st.session_state[f"ai_{target}_{name}"] = value


def choose_theme(target, theme):
    for field, value in {"theme": theme["theme"], "audience": theme["audience"], "problem": theme["problem"],
                         "keyword": "、".join(theme["keywords"]), "search_intent": theme["search_intent"]}.items():
        set_value(target, field, value)
    select_step(target, STEPS[1])


def choose_title(target, item):
    set_value(target, "title", item["title"])
    set_value(target, "search_intent", item["search_intent"])
    select_step(target, STEPS[2])


def select_step(target, step):
    st.session_state.ai_workspaces[target]["step"] = step
    st.session_state[f"ai_step_{target}"] = step


def adopt_outline(target):
    space = st.session_state.ai_workspaces[target]
    set_value(target, "outline", space["values"]["generated_outline"])
    select_step(target, STEPS[3])


def adopt_body(target, append):
    v = st.session_state.ai_workspaces[target]["values"]
    result = v["generated_body"]
    set_value(target, "body", (v["body"].rstrip() + "\n\n" + result).strip() if append else result)


def _apply_to_editor(store, target):
    """Called as a callback; never writes over a saved article implicitly."""
    v = st.session_state.ai_workspaces[target]["values"]
    if not (v["title"].strip() or v["theme"].strip()):
        st.session_state.ai_apply_error = "タイトルまたはテーマを入力してください。"
        return
    drafts = st.session_state.drafts
    if target not in drafts:
        saved = store.get(int(target)) if target != "new" else None
        if target != "new" and saved is None:
            st.session_state.ai_apply_error = "反映先の記事が削除されています。新しい記事を選んでください。"
            return
        space = st.session_state.ai_workspaces[target]
        drafts[target] = {"values": copy.deepcopy(space["source"]),
                          "version": space["version"], "dirty": False}
    draft = drafts[target]
    for name in ("genre", "audience", "keyword", "search_intent", "outline", "body"):
        draft["values"][name] = v[name]
    draft["values"]["title"] = v["title"].strip() or v["theme"].strip()
    draft["dirty"] = True
    for name in FIELDS:
        st.session_state.pop(f"edit_{target}_{name}", None)
    st.session_state.editor_id = None if target == "new" else int(target)
    st.session_state.page = "記事を書く・編集する"
    st.session_state.flash = "AI作業の内容を編集欄へ反映しました。確認して「記事を保存」を押してください。"


def apply_to_editor(store, target):
    try:
        _apply_to_editor(store, target)
    except (sqlite3.Error, OSError):
        st.session_state.ai_apply_error = "反映先の記事を開けませんでした。AIの作業内容は保持しています。保存先を確認してください。"


def render_ai(store):
    st.header("AI記事づくり")
    st.caption("テーマ → タイトル → 構成 → 本文。各段階で選び直し・手動編集できます。")
    articles = store.list()
    labels = {"new": "新しい記事"} | {str(a["id"]): f'{a["title"]}（ID {a["id"]}）' for a in articles}
    st.session_state.setdefault("ai_target", st.session_state.get("ai_selected_target", "new"))
    if st.session_state.ai_target not in labels:
        st.session_state.ai_target = "new"
    target = st.selectbox("作業する記事", list(labels), format_func=labels.get, key="ai_target")
    st.session_state.ai_selected_target = target
    space = workspace(store, target)
    v = space["values"]
    st.info("AIの入力・候補は画面移動中は保持されますが、再読み込みや終了で失われます。「記事編集へ反映」→「記事を保存」で本文などを保存してください。生成しただけでは記事は変更されません。")

    def remember(name, widget):
        v[name] = st.session_state[widget]

    def field(name, label, kind="text", **kwargs):
        key = f"ai_{target}_{name}"
        if key not in st.session_state:
            st.session_state[key] = v[name]
        common = {"key": key, "on_change": remember, "args": (name, key)}
        if kind == "area":
            return st.text_area(label, **common, **kwargs)
        if kind == "select":
            return st.selectbox(label, **common, **kwargs)
        if kind == "number":
            return st.number_input(label, **common, **kwargs)
        return st.text_input(label, **common, **kwargs)

    prefs = render_ai_settings()

    step_key = f"ai_step_{target}"
    st.session_state.setdefault(step_key, space["step"])
    def step_change():
        space["step"] = st.session_state[step_key]
    step = st.radio("作業の段階", STEPS, horizontal=True, key=step_key, on_change=step_change)
    kind = dict(zip(STEPS, ("themes", "titles", "outline", "body")))[step]
    with st.expander("企画の基本情報", expanded=kind == "themes"):
        field("genre", "記事ジャンル", "select", options=GENRES)
        field("audience", "読者の年代・想定読者")
        field("problem", "読者の悩み", "area", height=90)
        field("message", "記事で伝えたいメッセージ", "area", height=90)
        field("purpose", "記事の目的", "select", options=("共感", "悩み解決", "検索流入", "収益化"))
        field("keyword", "関連キーワード・メインキーワード（任意）")
    if kind != "themes":
        field("theme", "記事テーマ")
        field("search_intent", "狙う検索意図")
    if kind in ("outline", "body"):
        field("title", "確定タイトル（手動編集可）")
        field("word_count", "目安の文字数", "number", min_value=200, max_value=6000, step=100)
    if kind == "titles":
        st.caption("タイトルの文字数はアプリで数えます。AIの評価は参考で、検索順位を保証しません。")
        field("title", "選んだタイトル・手動タイトル")
        st.button("手動タイトルを確定して構成へ", disabled=not v["title"].strip(),
                  on_click=select_step, args=(target, STEPS[2]))
    if kind == "outline":
        field("outline", "現在の構成（修正の元・手動編集可）", "area", height=220)
        field("outline_action", "構成の作り方", "select", options=("新規・再生成", "一部修正"))
        if v["outline_action"] == "一部修正":
            field("revision", "修正したい箇所と内容", "area", height=90)
        st.button("現在の構成を確定して本文へ", disabled=not v["outline"].strip(), on_click=select_step, args=(target, STEPS[3]))
    if kind == "body":
        field("outline", "確定した構成（編集可）", "area", height=180)
        field("mode", "執筆モード", "select", options=ai_client.MODES)
        if v["mode"] == ai_client.MODES[2]:
            field("section", "執筆するH2・H3の見出し")
        if v["mode"] == ai_client.MODES[4]:
            field("existing_body", "続きの元になる文章", "area", height=160)
        if v["mode"] == ai_client.MODES[5]:
            field("memo", "文章にする箇条書きメモ", "area", height=160)
        with st.expander("自分の経験を入力する（入力した事実だけを使用）", expanded=True):
            for name, label in (("experience", "私が経験したこと"), ("experience_problem", "当時困っていたこと"),
                                ("experience_thought", "どのように考えたか"), ("experience_tried", "実際に試したこと"),
                                ("experience_message", "読者に伝えたいこと")):
                field(name, label, "area", height=90)
            st.caption("空欄の経験はAIに創作させません。必要な箇所は入力を求める文章になります。個人名などの不要な個人情報は除いてください。")
    if v["genre"] in ("健康と美容", "お金とこれからの生活"):
        st.warning("健康・美容・お金の効果や結果は断定せず、公開前に信頼できる根拠を確認してください。")
    request_values = dict(v) | {"tone": prefs.get("tone", "")}
    if kind == "outline":
        if v["outline_action"] == "新規・再生成":
            request_values["revision"] = ""
        elif not v["revision"].strip():
            request_values["revision"] = ""  # Validation below provides a visible, specific prompt.
    request = None
    try:
        if kind == "outline" and v["outline_action"] == "一部修正" and not v["revision"].strip():
            raise ai_client.GenerationError("修正したい箇所と内容を入力してください。")
        request = ai_client.prepare_request(kind, request_values, prefs["model"])
    except ai_client.GenerationError as exc:
        st.caption(str(exc))
    action = {"themes": "テーマ5案を生成", "titles": "SEOタイトルを生成", "outline": "構成を再生成", "body": "本文を生成"}[kind]
    if kind == "outline" and v["outline_action"] == "一部修正":
        action = "構成の一部を修正"
    generated = render_generation(request, space, f"{target}_{kind}", action)
    if generated is not None:
        space["results"][kind] = {"data": generated, "fingerprint": request.fingerprint, "input": request.input_json}
        if kind in ("outline", "body"):
            set_value(target, "generated_" + kind, generated[kind])
        st.rerun()

    result = space["results"].get(kind)
    if result:
        st.subheader("生成結果")
        st.caption("外部情報：未検証。公開前に内容・根拠・ご自身の経験との一致を確認してください。")
        stale = request is None or result["fingerprint"] != request.fingerprint
        if stale:
            st.warning("この候補の生成後に条件が変わっています。以前の結果を表示しています。新しい条件で生成するか、必要な内容を手動で入力してください。")
        st.download_button("生成結果をJSONで退避", json.dumps(result["data"], ensure_ascii=False, indent=2).encode("utf-8"),
                           file_name=f"miyabi_{kind}.json", mime="application/json", key=f"result_download_{target}_{kind}")
        if kind == "themes":
            for index, item in enumerate(result["data"]["themes"]):
                with st.container(border=True):
                    st.subheader(item["theme"])
                    for label, name in (("想定読者", "audience"), ("検索意図", "search_intent"), ("具体的な悩み", "problem"),
                                        ("読むメリット", "benefit"), ("記事の方向性", "direction"), ("無料・有料記事との相性", "free_paid_fit")):
                        st.write(f"{label}：{item[name]}")
                    st.write("SEOキーワード候補：" + "、".join(item["keywords"]))
                    st.button("この企画を選んでタイトルへ", key=f"theme_{target}_{index}", disabled=stale,
                              on_click=choose_theme, args=(target, item))
        elif kind == "titles":
            for index, item in enumerate(result["data"]["titles"]):
                with st.container(border=True):
                    st.subheader(item["title"])
                    st.caption(f'{len(item["title"])}文字')
                    st.write("検索意図：" + item["search_intent"])
                    st.write("タイトルの魅力：" + item["appeal"])
                    st.write("改善ポイント：" + item["improvement"])
                    st.button("このタイトルを選ぶ", key=f"title_{target}_{index}", disabled=stale,
                              on_click=choose_title, args=(target, item))
        elif kind == "outline":
            field("generated_outline", "生成された構成（自由に編集できます）", "area", height=300)
            for check in result["data"]["checks"]:
                st.write(f'{check["item"]}：{check["assessment"]}')
            st.button("構成を確定", on_click=adopt_outline, args=(target,), disabled=stale)
        elif kind == "body":
            field("generated_body", "生成された本文（編集可）", "area", height=350)
            for question in result["data"]["experience_questions"]:
                st.info("ご自身への質問：" + question)
            confirm = st.checkbox("現在の本文を置き換えることを確認しました", key=f"replace_body_{target}")
            c1, c2 = st.columns(2)
            c1.button("この結果で本文を置き換える", on_click=adopt_body, args=(target, False), disabled=stale or not confirm)
            c2.button("この結果を本文の末尾に追加", on_click=adopt_body, args=(target, True), disabled=stale)
    if kind == "body":
        st.subheader("記事として採用する本文")
        field("body", "採用する本文（手動編集可）", "area", height=300)
    st.divider()
    st.subheader("記事の編集・保存へ")
    st.caption("反映する項目：タイトル（空欄ならテーマ）、ジャンル、対象読者、キーワード、検索意図、構成、本文。ハッシュタグ・公開情報・備考は保持します。選択した記事の編集欄にある同じ項目は置き換わります。")
    st.download_button("作業中の本文をMarkdownで退避", article_markdown({"title": v["title"] or v["theme"], "body": v["body"]}),
                       file_name="miyabi_ai_draft.md", mime="text/markdown", key=f"ai_draft_export_{target}")
    confirmed = st.checkbox("選択した記事の編集欄に反映することを確認しました", key=f"apply_confirm_{target}")
    if "ai_apply_error" in st.session_state:
        st.error(st.session_state.pop("ai_apply_error"))
    st.button("記事編集へ反映", disabled=not confirmed, on_click=apply_to_editor, args=(store, target), type="primary")
