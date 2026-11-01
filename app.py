"""Run with: streamlit run app.py"""
from pathlib import Path
import os
import sqlite3

from dotenv import load_dotenv
import streamlit as st

from miyabi.database import ArticleStore
from miyabi.ui import render_app
from miyabi.settings import resolve_data_dir

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=False)
st.set_page_config(page_title="みやび AIライティングスタジオ", page_icon="🌷", layout="wide")
try:
    st.session_state.setdefault("_runtime_data_dir", str(resolve_data_dir(ROOT)))
    data_dir = Path(st.session_state._runtime_data_dir)
    store = ArticleStore(data_dir / "miyabi.sqlite3")
except (OSError, sqlite3.Error, ValueError):
    st.error("保存先を開けません。空き容量とフォルダーの書き込み権限、local_config.json と .env の MIYABI_DATA_DIR を確認してください。既存のデータは削除していません。")
    st.stop()
render_app(store)
