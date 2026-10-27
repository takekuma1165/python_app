import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from miyabi.database import ArticleStore

ROOT = Path(__file__).resolve().parents[1]


class UiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        env = patch.dict(os.environ, {"MIYABI_DATA_DIR": self.temp.name, "OPENAI_API_KEY": ""})
        env.start()
        self.addCleanup(env.stop)
        self.app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=20)
        self.store = ArticleStore(Path(self.temp.name) / 'miyabi.sqlite3')
        self.assert_no_error()

    def assert_no_error(self):
        self.assertFalse(self.app.exception, [e.message for e in self.app.exception])

    def button(self, label):
        return next(b for b in self.app.button if b.label == label)

    def navigate(self, name):
        self.app.radio(key='page').set_value(name).run()
        self.assert_no_error()

    def new(self):
        self.button('＋ 新しい記事を書く').click().run()
        self.assert_no_error()

    def test_create_edit_reopen_export_duplicate_and_confirm_delete(self):
        self.new()
        self.app.text_input(key='edit_new_title').set_value('わたしの新しい一歩')
        self.app.text_area(key='edit_new_body').set_value('## はじめに\n経験から伝えたいこと。')
        self.button('記事を保存').click().run()
        self.assert_no_error()
        a = self.store.list()[0]
        self.assertEqual(a['title'], 'わたしの新しい一歩')
        key = f"edit_{a['id']}_body"
        self.app.text_area(key=key).set_value('編集後の文章')
        self.button('記事を保存').click().run()
        self.assert_no_error()
        self.assertEqual(self.store.get(a['id'])['body'], '編集後の文章')
        self.navigate('出力・投稿準備')
        self.assertEqual(len(self.app.get('download_button')), 2)
        self.assertIn('編集後の文章', self.app.text_area[0].value)
        self.navigate('記事一覧')
        self.button('複製').click().run()
        self.assert_no_error()
        self.assertEqual(len(self.store.list()), 2)
        self.assertIn('（コピー）', self.app.text_input[0].value)
        self.navigate('記事一覧')
        copied = next(a for a in self.store.list() if '（コピー）' in a['title'])
        self.app.button(key=f"delete_{copied['id']}").click().run()
        self.assertEqual(len(self.store.list()), 2)
        self.app.checkbox(key=f"confirm_{copied['id']}").check().run()
        self.app.button(key=f"final_delete_{copied['id']}").click().run()
        self.assert_no_error()
        self.assertEqual(len(self.store.list()), 1)

    def test_unsaved_input_survives_navigation_and_failed_save(self):
        self.new()
        self.app.text_area(key='edit_new_body').set_value('消えてはいけない下書き').run()
        self.navigate('ホーム')
        self.button('下書きに戻る：無題の下書き').click().run()
        self.assertEqual(self.app.text_area(key='edit_new_body').value, '消えてはいけない下書き')
        self.button('記事を保存').click().run()
        self.assertTrue(self.app.error)
        self.assertEqual(self.store.list(), [])
        self.app.text_input(key='edit_new_title').set_value('保存失敗テスト').run()
        with patch.object(ArticleStore, 'save', side_effect=sqlite3.OperationalError('secret error details')):
            self.button('記事を保存').click().run()
        self.assert_no_error()
        self.assertTrue(self.app.error)
        self.assertNotIn('secret error details', self.app.error[0].value)
        self.assertEqual(self.app.text_area(key='edit_new_body').value, '消えてはいけない下書き')
        self.button('記事を保存').click().run()
        self.assert_no_error()
        self.assertEqual(self.store.list()[0]['body'], '消えてはいけない下書き')

    def test_all_pages_work_without_api_key_and_reopen_persisted_article(self):
        self.new()
        self.app.text_input(key='edit_new_title').set_value('再起動確認')
        self.button('記事を保存').click().run()
        fresh = AppTest.from_file(str(ROOT / 'app.py')).run()
        self.assertFalse(fresh.exception)
        self.assertIn('再起動確認', [h.value for h in fresh.markdown])
        for page in ('ホーム', '記事一覧', '出力・投稿準備', 'このアプリについて'):
            self.navigate(page)
        self.assertTrue(any('未設定' in m.value for m in self.app.markdown))


if __name__ == '__main__':
    unittest.main()
