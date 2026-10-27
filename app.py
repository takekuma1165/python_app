"""Run with: streamlit run app.py"""
from pathlib import Path
import os
import sqlite3

from dotenv import load_dotenv
import streamlit as st

from miyabi.database import ArticleStore
from miyabi.ui import render_app

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=False)
st.set_page_config(page_title="みやび AIライティングスタジオ", page_icon="🌷", layout="wide")
data_dir = Path(os.environ.get("MIYABI_DATA_DIR", "data")).expanduser()
if not data_dir.is_absolute():
    data_dir = ROOT / data_dir
try:
    store = ArticleStore(data_dir / "miyabi.sqlite3")
except (OSError, sqlite3.Error):
    st.error("保存先を開けません。空き容量とフォルダーの書き込み権限、.env の MIYABI_DATA_DIR を確認してください。既存のデータは削除していません。")
    st.stop()
render_app(store)
