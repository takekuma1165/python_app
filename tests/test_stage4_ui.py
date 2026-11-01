import copy
import io
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from miyabi.backup import backup_bytes, validate_backup
from miyabi.database import ArticleStore, empty_article
from publication_fixtures import PUBLICATION

ROOT = Path(__file__).resolve().parents[1]


class Stage4UiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.env = patch.dict(os.environ, {'MIYABI_DATA_DIR': self.temp.name, 'OPENAI_API_KEY': '', 'MIYABI_CONFIG_PATH': str(Path(self.temp.name) / 'local_config.json')})
        self.env.start(); self.addCleanup(self.env.stop)
        self.store = ArticleStore(Path(self.temp.name) / 'miyabi.sqlite3')
        self.i = self.store.save(empty_article() | {'title': '暮らしの工夫', 'body': '本人が考えた暮らしの工夫です。', 'notes': '送信しない備考'})
        self.app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=20)
        self.clean()

    def clean(self): self.assertFalse(self.app.exception, [e.message for e in self.app.exception])
    def button(self, label): return next(b for b in self.app.button if b.label == label)
    def checkbox(self, label): return next(c for c in self.app.checkbox if c.label == label)
    def page(self, name): self.app.radio(key='page').set_value(name).run(); self.clean()

    def test_manual_publication_saves_and_survives_new_session_without_api(self):
        self.page('出力・投稿準備')
        self.app.text_area(key=f'pub_{self.i}_introduction').set_value('手動で書いた紹介文').run()
        self.app.text_area(key=f'pub_{self.i}_thread_1').set_value('手動の告知文').run()
        self.button('投稿準備を保存').click().run(); self.clean()
        self.assertEqual(self.store.publication(self.i)['data']['introduction'], '手動で書いた紹介文')
        self.assertEqual(self.store.get(self.i)['body'], '本人が考えた暮らしの工夫です。')
        self.app = AppTest.from_file(str(ROOT / 'app.py')).run()
        self.page('出力・投稿準備')
        self.assertEqual(self.app.text_area(key=f'pub_{self.i}_thread_1').value, '手動の告知文')
        self.assertEqual(len(self.app.get('download_button')), 3)

    def test_generate_promotions_preserves_body_and_undo_restores_prior_draft(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-not-real'}):
            self.page('出力・投稿準備')
            self.app.checkbox(key='ai_pref_enabled').check().run()
            self.button('送信内容を確認').click().run()
            self.checkbox('送信内容と料金発生を確認しました').check().run()
            with patch('miyabi.ai_client.generate', return_value=copy.deepcopy(PUBLICATION)) as api:
                self.button('投稿準備の候補を生成').click().run()
            self.clean(); self.assertEqual(api.call_count, 1)
            self.assertNotIn('送信しない備考', api.call_args.args[0].input_json)
            self.assertEqual(self.app.text_area(key=f'pub_{self.i}_body').value, '本人が考えた暮らしの工夫です。')
            self.assertEqual(self.app.text_area(key=f'pub_{self.i}_thread_2').value, PUBLICATION['threads'][1])
            self.assertIsNone(self.store.publication(self.i))
            self.button('前の投稿準備に戻す').click().run(); self.clean()
            self.assertEqual(self.app.text_area(key=f'pub_{self.i}_thread_2').value, '')

    def test_publication_save_failure_and_article_change_keep_inputs(self):
        self.page('出力・投稿準備')
        self.app.text_area(key=f'pub_{self.i}_introduction').set_value('消さない紹介文').run()
        with patch.object(ArticleStore, 'save_publication', side_effect=sqlite3.OperationalError('private-details')):
            self.button('投稿準備を保存').click().run()
        self.clean(); self.assertTrue(self.app.error)
        self.assertNotIn('private-details', self.app.error[0].value)
        self.assertEqual(self.app.text_area(key=f'pub_{self.i}_introduction').value, '消さない紹介文')
        self.store.save(self.store.get(self.i) | {'body': '更新された元記事'}, self.i)
        self.app.run(); self.button('投稿準備を保存').click().run(); self.clean()
        self.assertTrue(self.app.error)
        self.assertIsNone(self.store.publication(self.i))
        self.checkbox('投稿準備のタイトル・本文・タグを最新記事で置き換えます').check().run()
        self.button('最新記事のタイトル・本文・タグを取り込む').click().run()
        self.assertEqual(self.app.text_area(key=f'pub_{self.i}_body').value, '更新された元記事')
        self.assertEqual(self.app.text_area(key=f'pub_{self.i}_introduction').value, '消さない紹介文')
        self.button('投稿準備を保存').click().run(); self.clean()
        self.assertIsNotNone(self.store.publication(self.i))

    def test_saved_defaults_apply_to_new_article_and_ai_workspace(self):
        self.page('設定・バックアップ')
        self.app.text_input(key='settings_audience').set_value('60代の女性').run()
        self.app.text_area(key='settings_tone').set_value('落ち着いた温かい文章').run()
        self.app.number_input(key='settings_word_count').set_value(1500).run()
        self.app.text_input(key='settings_model').set_value('custom-model').run()
        self.button('設定を保存').click().run(); self.clean()
        self.app = AppTest.from_file(str(ROOT / 'app.py')).run()
        self.page('記事を書く・編集する')
        self.assertEqual(self.app.text_input(key='edit_new_audience').value, '60代の女性')
        self.page('AI記事づくり')
        self.assertEqual(self.app.text_input(key='ai_new_audience').value, '60代の女性')
        self.assertEqual(self.app.text_input(key='ai_pref_model').value, 'custom-model')
        self.app.radio(key='ai_step_new').set_value('④ 本文執筆').run(); self.clean()
        self.assertEqual(self.app.number_input(key='ai_new_word_count').value, 1500)

    def test_backup_download_contains_publications_and_restore_is_confirmed(self):
        self.page('出力・投稿準備')
        self.app.text_area(key=f'pub_{self.i}_introduction').set_value('復元する紹介文').run()
        self.button('投稿準備を保存').click().run()
        self.page('設定・バックアップ')
        self.button('最新のバックアップを作成').click().run(); self.clean()
        raw = self.app.session_state['backup_download']['raw']
        self.assertEqual(validate_backup(raw)['publications'][0]['data']['introduction'], '復元する紹介文')
        self.store.save(empty_article() | {'title': 'バックアップ後の記事'})
        uploaded = io.BytesIO(raw); uploaded.name = 'miyabi-backup.json'
        with patch('streamlit.file_uploader', return_value=uploaded):
            self.app.run(); self.button('復元する内容を確認').click().run(); self.clean()
            self.assertTrue(self.button('全データを復元する').disabled)
            self.assertEqual(len(self.store.list()), 2)
            self.checkbox('未保存の作業を退避し、現在の全データを置き換えることを確認しました').check().run()
            self.button('全データを復元する').click().run(); self.clean()
        self.assertEqual(len(self.store.list()), 1)
        self.assertEqual(self.store.publication(self.i)['data']['introduction'], '復元する紹介文')
        self.assertTrue(list((Path(self.temp.name) / 'backups').glob('before-restore-*.json')))
        self.assertNotIn('publication_spaces', self.app.session_state)

    def test_bad_backup_shows_error_without_data_loss(self):
        self.page('設定・バックアップ')
        uploaded = io.BytesIO(b'{"not":"a backup"}'); uploaded.name = 'bad.json'
        with patch('streamlit.file_uploader', return_value=uploaded):
            self.app.run(); self.button('復元する内容を確認').click().run(); self.clean()
        self.assertTrue(self.app.error)
        self.assertEqual(len(self.store.list()), 1)
        self.assertFalse(any(b.label == '全データを復元する' for b in self.app.button))

    def test_storage_copy_requires_restart_and_new_session_uses_copied_data(self):
        pointer = Path(self.temp.name) / 'local_config.json'
        pointer.write_text(__import__('json').dumps({'data_dir': self.temp.name}))
        with patch.dict(os.environ, {'MIYABI_DATA_DIR': ''}):
            self.page('設定・バックアップ')
            destination = Path(self.temp.name) / 'copied'
            self.app.text_input(key='settings_new_folder').set_value(str(destination)).run()
            self.checkbox('未保存の入力を保存済みで、コピー後に再起動します').check().run()
            self.button('新しい保存先へコピーして設定').click().run(); self.clean()
            self.assertTrue((destination / 'miyabi.sqlite3').exists())
            self.app.run(); self.clean()
            self.assertTrue(any('再起動' in w.value for w in self.app.warning))
            self.assertFalse(self.app.radio)
            fresh = AppTest.from_file(str(ROOT / 'app.py')).run(); self.assertFalse(fresh.exception)
            self.assertEqual(fresh.session_state['_runtime_data_dir'], str(destination))
            self.assertEqual(ArticleStore(destination / 'miyabi.sqlite3').get(self.i)['title'], '暮らしの工夫')

    def test_dashboard_shows_separate_counts_and_recommendation_creates_idea(self):
        self.assertEqual({m.label for m in self.app.metric}, {'保存した記事', '作成中', '完成', '公開済み', '今月作成'})
        self.button('このテーマをアイデアとして保存').click().run(); self.clean()
        self.assertEqual(len(self.store.list()), 2)
        self.assertEqual(self.app.radio(key='page').value, '記事を書く・編集する')
        self.assertEqual(self.app.selectbox[1].value, 'アイデア')


if __name__ == '__main__': unittest.main()
