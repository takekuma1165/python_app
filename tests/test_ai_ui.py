import copy
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from miyabi.database import ArticleStore, empty_article
from miyabi.ai_client import GenerationError, MODES
from ai_fixtures import RESULTS

ROOT = Path(__file__).resolve().parents[1]


class AiUiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        env = patch.dict(os.environ, {'MIYABI_DATA_DIR': self.temp.name, 'OPENAI_API_KEY': 'test-only-key'})
        env.start(); self.addCleanup(env.stop)
        self.store = ArticleStore(Path(self.temp.name) / 'miyabi.sqlite3')
        self.app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=20)
        self.app.radio(key='page').set_value('AI記事づくり').run()
        self.clean()

    def clean(self):
        self.assertFalse(self.app.exception, [e.message for e in self.app.exception])

    def button(self, label):
        return next(b for b in self.app.button if b.label == label)

    def checkbox(self, label):
        return next(c for c in self.app.checkbox if c.label == label)

    def configure(self):
        self.app.checkbox(key='ai_pref_enabled').check().run()
        self.app.text_area(key='ai_new_problem').set_value('暮らしを整えたい').run()

    def preview_consent(self):
        self.button('送信内容を確認').click().run(); self.clean()
        self.checkbox('送信内容と料金発生を確認しました').check().run()

    def generate(self, kind, label):
        self.preview_consent()
        with patch('miyabi.ai_client.generate', return_value=copy.deepcopy(RESULTS[kind])) as api:
            self.button(label).click().run()
        self.clean(); self.assertEqual(api.call_count, 1)
        return api.call_args.args[0]

    def test_four_step_workflow_edits_facts_and_persists_adopted_article(self):
        self.configure()
        self.generate('themes', 'テーマ5案を生成')
        self.app.button(key='theme_new_0').click().run(); self.clean()
        self.assertEqual(self.app.radio(key='ai_step_new').value, '② SEOタイトル')
        self.generate('titles', 'SEOタイトルを生成')
        self.app.button(key='title_new_0').click().run(); self.clean()
        self.app.text_input(key='ai_new_title').set_value('手で整えたタイトル').run()
        self.generate('outline', '構成を再生成')
        self.app.text_area(key='ai_new_generated_outline').set_value('# 手で整えた構成\n## 私の一歩').run()
        self.button('構成を確定').click().run(); self.clean()
        self.assertEqual(self.app.radio(key='ai_step_new').value, '④ 本文執筆')
        self.app.text_area(key='ai_new_experience').set_value('引き出しを一つ整理した').run()
        request = self.generate('body', '本文を生成')
        self.assertIn('引き出しを一つ整理した', request.input_json)
        self.assertIn('手で整えた構成', request.input_json)
        self.app.text_area(key='ai_new_generated_body').set_value('本人が確認した体験の本文').run()
        self.checkbox('現在の本文を置き換えることを確認しました').check().run()
        self.button('この結果で本文を置き換える').click().run(); self.clean()
        self.checkbox('選択した記事の編集欄に反映することを確認しました').check().run()
        self.button('記事編集へ反映').click().run(); self.clean()
        self.assertEqual(self.store.list(), [])
        self.assertEqual(self.app.text_area(key='edit_new_body').value, '本人が確認した体験の本文')
        self.button('記事を保存').click().run(); self.clean()
        saved = self.store.list()[0]
        self.assertEqual(saved['title'], '手で整えたタイトル')
        self.assertEqual(saved['body'], '本人が確認した体験の本文')
        self.assertIn('手で整えた構成', saved['outline'])

    def test_no_api_key_no_request_and_manual_edit_still_available(self):
        self.configure()
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}), patch('miyabi.ai_client.generate') as api:
            self.preview_consent()
            self.assertTrue(self.button('テーマ5案を生成').disabled)
            api.assert_not_called()
            self.app.radio(key='page').set_value('記事を書く・編集する').run()
            self.app.text_input(key='edit_new_title').set_value('APIなしの記事')
            self.button('記事を保存').click().run(); self.clean()
        self.assertEqual(self.store.list()[0]['title'], 'APIなしの記事')

    def test_changed_input_or_model_invalidates_consent_and_no_call_on_navigation(self):
        self.configure()
        with patch('miyabi.ai_client.generate') as api:
            self.preview_consent()
            self.assertFalse(self.button('テーマ5案を生成').disabled)
            self.app.text_area(key='ai_new_problem').set_value('別の悩み').run()
            self.assertFalse(any(b.label == 'テーマ5案を生成' for b in self.app.button))
            self.preview_consent()
            self.app.text_input(key='ai_pref_model').set_value('another-model').run()
            self.assertFalse(any(b.label == 'テーマ5案を生成' for b in self.app.button))
            self.app.radio(key='page').set_value('ホーム').run()
            self.app.radio(key='page').set_value('AI記事づくり').run(); self.clean()
            self.assertEqual(self.app.text_area(key='ai_new_problem').value, '別の悩み')
            api.assert_not_called()

    def test_failed_regeneration_keeps_previous_output_and_does_not_touch_database(self):
        i = self.store.save(empty_article() | {'title': '保存済み', 'body': '守る文章'})
        self.configure()
        self.generate('themes', 'テーマ5案を生成')
        self.preview_consent()
        with patch('miyabi.ai_client.generate', side_effect=GenerationError('利用上限に達しました')):
            self.button('テーマ5案を生成').click().run()
        self.clean()
        self.assertTrue(any('利用上限' in e.value for e in self.app.error))
        self.assertEqual(len([b for b in self.app.button if b.label == 'この企画を選んでタイトルへ']), 5)
        self.assertEqual(self.store.get(i)['body'], '守る文章')
        self.app.run()
        self.assertFalse(any(b.label == 'テーマ5案を生成' for b in self.app.button))
        self.button('送信内容を確認').click().run()
        self.assertFalse(self.checkbox('送信内容と料金発生を確認しました').value)

    def test_existing_article_privacy_and_explicit_adoption_keep_metadata(self):
        i = self.store.save(empty_article() | {'title': '既存の記事', 'body': '既存本文', 'notes': '機密の備考',
                                             'hashtags': '#暮らし', 'status': '完成'})
        self.app.run()
        self.app.selectbox(key='ai_target').set_value(str(i)).run()
        self.app.radio(key=f'ai_step_{i}').set_value('④ 本文執筆').run()
        self.app.checkbox(key='ai_pref_enabled').check().run()
        self.app.selectbox(key=f'ai_{i}_mode').set_value(MODES[4]).run()
        self.preview_consent()
        with patch('miyabi.ai_client.generate', return_value=copy.deepcopy(RESULTS['body'])) as api:
            self.button('本文を生成').click().run()
        request = api.call_args.args[0]
        self.assertIn('既存本文', request.input_json)
        self.assertNotIn('機密の備考', request.input_json)
        self.button('この結果を本文の末尾に追加').click().run()
        self.checkbox('選択した記事の編集欄に反映することを確認しました').check().run()
        self.button('記事編集へ反映').click().run(); self.clean()
        self.assertEqual(self.store.get(i)['body'], '既存本文')
        self.button('記事を保存').click().run(); self.clean()
        saved = self.store.get(i)
        self.assertTrue(saved['body'].startswith('既存本文\n\n'))
        self.assertEqual(saved['notes'], '機密の備考')
        self.assertEqual(saved['hashtags'], '#暮らし')
        self.assertEqual(saved['status'], '完成')

    def test_external_article_update_during_ai_work_is_not_overwritten(self):
        i = self.store.save(empty_article() | {'title': '元の記事', 'body': '最初の本文'})
        self.app.run()
        self.app.selectbox(key='ai_target').set_value(str(i)).run()
        self.store.save(empty_article() | {'title': '別画面のタイトル', 'body': '別画面からの更新'}, i)
        self.checkbox('選択した記事の編集欄に反映することを確認しました').check().run()
        self.button('記事編集へ反映').click().run(); self.clean()
        self.button('記事を保存').click().run(); self.clean()
        self.assertTrue(any('他の画面' in e.value for e in self.app.error))
        self.assertEqual(self.store.get(i)['body'], '別画面からの更新')
        self.assertEqual(self.app.text_area(key=f'edit_{i}_body').value, '最初の本文')

    def test_saved_article_ai_selection_survives_visiting_another_page(self):
        i = self.store.save(empty_article() | {'title': '選択を保持する記事', 'body': '入力済みの本文'})
        self.app.run()
        self.app.selectbox(key='ai_target').set_value(str(i)).run()
        self.app.text_area(key=f'ai_{i}_problem').set_value('保持する悩み').run()
        self.app.radio(key='page').set_value('ホーム').run()
        self.app.radio(key='page').set_value('AI記事づくり').run(); self.clean()
        self.assertEqual(self.app.selectbox(key='ai_target').value, str(i))
        self.assertEqual(self.app.text_area(key=f'ai_{i}_problem').value, '保持する悩み')

    def test_six_modes_and_partial_outline_send_expected_inputs(self):
        self.configure()
        self.app.radio(key='ai_step_new').set_value('④ 本文執筆').run()
        self.app.text_input(key='ai_new_title').set_value('タイトル').run()
        for mode in MODES:
            self.app.selectbox(key='ai_new_mode').set_value(mode).run()
            if mode == MODES[2]: self.app.text_input(key='ai_new_section').set_value('## 指定見出し').run()
            if mode == MODES[4]: self.app.text_area(key='ai_new_existing_body').set_value('元の本文').run()
            if mode == MODES[5]: self.app.text_area(key='ai_new_memo').set_value('・試したこと').run()
            request = self.generate('body', '本文を生成')
            self.assertIn(mode, request.input_json)
        self.app.radio(key='ai_step_new').set_value('③ 記事構成').run()
        self.app.text_area(key='ai_new_outline').set_value('## 元の構成').run()
        self.app.selectbox(key='ai_new_outline_action').set_value('一部修正').run()
        self.app.text_area(key='ai_new_revision').set_value('最後の見出しだけ修正').run()
        request = self.generate('outline', '構成の一部を修正')
        self.assertIn('最後の見出しだけ修正', request.input_json)
        self.assertIn('元の構成', request.input_json)


if __name__ == '__main__':
    unittest.main()
