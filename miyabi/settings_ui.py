"""Persistent defaults, safe folder copying and validated full-data restore."""
from pathlib import Path
import hashlib
import json
import os
import sqlite3
import streamlit as st
from miyabi import ai_client
from miyabi.backup import backup_bytes, fingerprint, restore_backup, snapshot, validate_backup
from miyabi.settings import DEFAULT_SETTINGS, move_data_folder

SETTINGS_PAGE = "設定・バックアップ"
ROOT = Path(__file__).resolve().parents[1]


def render_settings(store):
    st.header("設定・バックアップ")
    if "settings_draft" not in st.session_state:
        _, version = store.settings()
        st.session_state.settings_draft = {"values": dict(st.session_state["saved_settings"]), "version": version}
    draft = st.session_state.settings_draft; v = draft["values"]
    def changed(field):
        v[field] = st.session_state[f"settings_{field}"]
    for field in DEFAULT_SETTINGS:
        st.session_state.setdefault(f"settings_{field}", v[field])
    st.caption("設定はこのデータベースへ保存します。変更した標準値は新しく始めるAI企画・新規記事へ反映し、作業中の入力は書き換えません。")
    st.text_input("標準AIモデル", key="settings_model", on_change=changed, args=("model",))
    st.checkbox("標準でOpenAI APIの利用を有効にする", key="settings_ai_enabled", on_change=changed, args=("ai_enabled",))
    st.text_area("標準の文章トーン", key="settings_tone", on_change=changed, args=("tone",))
    st.text_input("標準の想定読者", key="settings_audience", on_change=changed, args=("audience",))
    st.number_input("標準文字数", min_value=200, max_value=6000, step=100, key="settings_word_count", on_change=changed, args=("word_count",))
    if st.button("設定を保存", type="primary"):
        try:
            draft["version"] = store.save_settings(v, draft["version"])
        except (ValueError, sqlite3.Error, OSError) as exc:
            st.error(str(exc) if isinstance(exc, ValueError) else "設定を保存できませんでした。入力は残しています。")
        else:
            st.session_state.saved_settings = dict(v)
            st.session_state.ai_preferences = {"model": v["model"], "enabled": v["ai_enabled"], "tone": v["tone"]}
            st.session_state.pop("ai_pref_model", None); st.session_state.pop("ai_pref_enabled", None)
            st.success("設定を保存しました。")
    if st.button("保存済み設定を読み込み直す"):
        st.session_state.pop("settings_draft", None)
        for field in DEFAULT_SETTINGS:
            st.session_state.pop(f"settings_{field}", None)
        st.rerun()
    st.subheader("AI生成時の注意事項")
    st.write("APIキーは環境変数または .env だけで管理します。ここやバックアップには保存しません。キーの変更は configure_api_windows.bat で行い、アプリを再起動してください。")
    st.caption("APIキー：" + ("設定あり（値は表示しません）" if ai_client.api_key_configured() else "未設定。手動編集・保存とローカル重複チェックは使えます。"))
    st.write("ChatGPTの有料プランとは別のAPI料金が発生します。送信データと料金を確認してから実行してください。実体験や出典を創作させず、生成内容は未検証として本人が確認してください。健康・美容・お金の効果を断定しないようにしましょう。")
    st.link_button("API料金を確認", "https://openai.com/api/pricing/")
    st.subheader("データ保存先")
    st.code(str(store.path), language=None)
    st.caption("保存先を変える場合は、現在の記事・投稿準備・設定を新しいフォルダーへコピーします。元のデータは残し、既存ファイルへの上書きは行いません。コピー後はアプリを停止して再起動してください。")
    if os.environ.get("MIYABI_DATA_DIR", "").strip():
        st.info("MIYABI_DATA_DIR が環境変数または .env で指定されています。そちらの指定が優先です。画面で変更する場合は指定行を削除またはコメントにして再起動してください。")
    else:
        folder = st.text_input("新しい保存先フォルダー", key="settings_new_folder", placeholder="C:/Users/YourName/Documents/MiyabiData")
        confirm_folder = st.checkbox("未保存の入力を保存済みで、コピー後に再起動します", key="settings_folder_confirm")
        if st.button("新しい保存先へコピーして設定", disabled=not confirm_folder or not folder.strip()):
            try:
                target = move_data_folder(store, ROOT, folder)
            except FileExistsError:
                st.error("その保存先にはすでにデータベースがあります。別の空のフォルダーを指定してください。")
            except (ValueError, OSError, sqlite3.Error) as exc:
                st.error(str(exc) if isinstance(exc, ValueError) else "コピーまたは保存先の設定に失敗しました。元のデータは残っています。新しい保存先も確認してください。")
            else:
                st.session_state.storage_move_pending = str(target)
                st.success(f"コピーしました：{target}。黒い画面でCtrl+Cを押し、start_windows.bat で起動し直してください。")
    render_backup(store)


def render_backup(store):
    st.subheader("バックアップをダウンロード")
    st.caption("保存済みの記事（備考を含む）・投稿準備・標準設定をJSON形式でまとめます。APIキー・.env・保存先設定・未保存の下書きは含みません。個人情報が含まれるため安全な場所で保管してください。")
    if st.button("最新のバックアップを作成"):
        try:
            raw = backup_bytes(store)
            st.session_state.backup_download = {"path": str(store.path), "raw": raw}
        except (ValueError, OSError, sqlite3.Error):
            st.error("バックアップを作成できませんでした。保存先の状態とデータ量を確認してください（最大32MB）。")
    download = st.session_state.get("backup_download")
    if download and download["path"] == str(store.path):
        st.download_button("バックアップJSONをダウンロード", download["raw"], file_name="miyabi-backup.json", mime="application/json")
        st.caption("これは作成ボタンを押した時点の保存済みデータです。記事を更新した場合は作り直してください。")
    st.subheader("バックアップから復元")
    st.warning("復元は現在の記事・投稿準備・設定をすべて置き換えます。追加・合体ではありません。復元前のデータは backups フォルダーへ自動退避します。未保存の作業は退避してから進めてください。")
    upload = st.file_uploader("みやびのバックアップJSON（32MB以内）", type=["json"], key="restore_upload")
    if upload is None:
        return
    raw = upload.getvalue(); upload_hash = hashlib.sha256(raw).hexdigest()
    if st.button("復元する内容を確認"):
        try:
            data = validate_backup(raw)
            current = fingerprint(snapshot(store))
        except (ValueError, OSError, sqlite3.Error) as exc:
            st.error(str(exc) if isinstance(exc, ValueError) else "バックアップを確認できませんでした。現在のデータは変更していません。")
        else:
            st.session_state.restore_preview = {"hash": upload_hash, "expected": current, "articles": len(data["articles"]),
                                                "publications": len(data["publications"]), "settings": data["settings"] is not None}
    preview = st.session_state.get("restore_preview")
    if preview and preview["hash"] == upload_hash:
        st.write(f'復元する記事：{preview["articles"]}件 ／ 投稿準備：{preview["publications"]}件 ／ 保存設定：{"あり" if preview["settings"] else "なし"}')
        confirmed = st.checkbox("未保存の作業を退避し、現在の全データを置き換えることを確認しました", key=f"restore_confirm_{upload_hash}")
        if st.button("全データを復元する", disabled=not confirmed, type="primary"):
            try:
                safety = restore_backup(store, raw, preview["expected"])
            except (ValueError, OSError, sqlite3.Error) as exc:
                st.error(str(exc) if isinstance(exc, ValueError) else "復元できませんでした。現在のデータは変更していません。")
            else:
                # Clear all old drafts and API permissions bound to the previous database state.
                st.session_state.clear()
                st.session_state.page = SETTINGS_PAGE
                st.session_state.flash = f"復元しました。復元前データ：{safety}。他のタブも再読み込みしてください。"
                st.rerun()
