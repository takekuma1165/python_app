"""Shared model settings and one-use approval for each billable API attempt."""
import streamlit as st
from miyabi import ai_client


def render_ai_settings():
    prefs = st.session_state.setdefault("ai_preferences", {"model": ai_client.default_model(), "enabled": False})
    with st.expander("AI利用設定・APIキーの設定方法", expanded=not ai_client.api_key_configured()):
        for name in ("model", "enabled"):
            st.session_state.setdefault(f"ai_pref_{name}", prefs[name])
        def changed(name):
            prefs[name] = st.session_state[f"ai_pref_{name}"]
        st.text_input("OpenAIモデル名", key="ai_pref_model", on_change=changed, args=("model",))
        st.checkbox("OpenAI APIを利用する（従量課金）", key="ai_pref_enabled", on_change=changed, args=("enabled",))
        st.caption("設定はこのセッションだけ保持します。既定モデルは .env の OPENAI_MODEL で指定できます。利用可否はご契約により異なります。")
        if ai_client.api_key_configured():
            st.success("APIキー：設定あり（値は表示しません）")
        else:
            st.warning("APIキーは未設定です。手動編集・保存とローカル重複チェックは利用できます。")
        st.write("キーはチャットへ貼らず、configure_api_windows.bat で .env を開いて OPENAI_API_KEY を設定し、アプリを再起動してください。")
        st.link_button("OpenAI APIキーの管理画面", "https://platform.openai.com/api-keys")
        st.link_button("OpenAI API料金を確認", "https://openai.com/api/pricing/")
        st.caption("ChatGPTの有料プランとは別にAPI利用料金がかかります。生成のたびに送信内容と料金発生の確認が必要です。")
    return prefs


def render_generation(request, space, scope, action):
    """Return a new response only on an approved click; never retry automatically."""
    if request is None:
        return None
    reviewed_key = f"reviewed_{scope}"
    if st.button("送信内容を確認", key=f"preview_{scope}"):
        space["review_counter"] = space.get("review_counter", 0) + 1
        space[reviewed_key] = (request.fingerprint, space["review_counter"])
    if space.get(reviewed_key, (None,))[0] != request.fingerprint:
        st.caption("入力やモデルを変えた場合は、もう一度「送信内容を確認」を押してください。")
        return None
    st.subheader("OpenAIに送信する内容")
    st.caption("下記以外の記事や備考を自動で送信することはありません。キーはAPI認証に使いますが表示対象には含めません。store: false で送りますが、OpenAI側の保持条件はサービスのポリシーをご確認ください。")
    with st.expander("送信データ全文（指示・素材・モデル・上限）", expanded=True):
        st.json(request.payload(), expanded=False)
    st.caption(f"出力トークン上限：{request.max_output_tokens:,}。文字数や料金そのものではありません。")
    consent = st.checkbox("送信内容と料金発生を確認しました",
                          key=f"consent_{scope}_{request.fingerprint}_{space[reviewed_key][1]}")
    prefs = st.session_state["ai_preferences"]
    ready = consent and prefs["enabled"] and ai_client.api_key_configured()
    if st.button(action, disabled=not ready, key=f"generate_{scope}", type="primary"):
        space.pop(reviewed_key, None)
        try:
            with st.spinner("AIの応答を待っています。完了まで画面を閉じずにお待ちください。"):
                return ai_client.generate(request)
        except ai_client.GenerationError as exc:
            st.error(str(exc))
    if not ready:
        st.caption("APIキーの設定、API利用の有効化、送信内容の確認がそろうと生成できます。")
    return None
