import copy
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from miyabi.ai_client import GenerationError
from miyabi.database import ArticleStore, empty_article
from review_fixtures import SOURCE, STYLE, PROOF, VALUES

ROOT = Path(__file__).resolve().parents[1]


class ReviewUiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        env = patch.dict(os.environ, {'MIYABI_DATA_DIR': self.temp.name, 'OPENAI_API_KEY': 'test-only-key'})
        env.start(); self.addCleanup(env.stop)
        self.store = ArticleStore(Path(self.temp.name) / 'miyabi.sqlite3')
        self.app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=20)
        self.page('みやび文体変換')

    def clean(self):
        self.assertFalse(self.app.exception, [e.message for e in self.app.exception])

    def button(self, label):
        return next(b for b in self.app.button if b.label == label)

    def checkbox(self, label):
        return next(c for c in self.app.checkbox if c.label == label)

    def page(self, name):
        self.app.radio(key='page').set_value(name).run(); self.clean()

    def input_body(self, body=SOURCE, target='new'):
        self.app.text_area(key=f'review_{target}_body').set_value(body).run(); self.clean()

    def preview(self):
        self.button('送信内容を確認').click().run(); self.clean()
        self.checkbox('送信内容と料金発生を確認しました').check().run()

    def generate(self, kind, data, action):
        self.app.checkbox(key='ai_pref_enabled').check().run()
        self.preview()
        with patch('miyabi.ai_client.generate', return_value=copy.deepcopy(data)) as api:
            self.button(action).click().run()
        self.clean(); self.assertEqual(api.call_count, 1)
        return api.call_args.args[0]

    def test_style_edit_adopt_undo_and_save_only_on_explicit_save(self):
        self.input_body()
        self.generate('style', STYLE, 'みやび文体に変換')
        self.assertEqual(next(t for t in self.app.text_area if t.label == '変更前（生成時の原文）').value, SOURCE)
        self.app.text_area(key='review_new_style_candidate').set_value('本人が確認した温かい文章').run()
        self.button('修正を採用').click().run(); self.clean()
        self.assertEqual(self.app.text_area(key='review_new_body').value, '本人が確認した温かい文章')
        self.assertEqual(self.store.list(), [])
        self.button('元に戻す').click().run(); self.clean()
        self.assertEqual(self.app.text_area(key='review_new_body').value, SOURCE)
        self.button('修正を採用').click().run()
        self.checkbox('選択した記事の編集欄の本文に反映します').check().run()
        self.button('本文を記事編集へ反映').click().run(); self.clean()
        self.assertEqual(self.store.list(), [])
        self.app.text_input(key='edit_new_title').set_value('文体変換の記事')
        self.button('記事を保存').click().run(); self.clean()
        self.assertEqual(self.store.list()[0]['body'], '本人が確認した温かい文章')

    def test_one_issue_at_a_time_exact_occurrence_and_overlaps(self):
        self.page('AI文章校正'); self.input_body()
        self.generate('proof', PROOF, '10項目でAI校正する')
        self.app.button(key='review_new_issue_1_1').click().run(); self.clean()
        body = self.app.text_area(key='review_new_body').value
        self.assertTrue(body.startswith('今日は公園に行きましした。'))
        self.assertTrue(body.endswith('今日は公園に行きました。'))
        self.app.button(key='review_new_issue_1_0').click().run(); self.clean()
        self.assertEqual(self.app.text_area(key='review_new_body').value.count('行きました'), 2)
        self.assertTrue(self.app.button(key='review_new_issue_1_2').disabled)
        self.button('元に戻す').click().run(); self.clean()
        self.assertEqual(self.app.text_area(key='review_new_body').value, body)
        self.assertFalse(self.app.button(key='review_new_issue_1_0').disabled)
        self.button('元に戻す').click().run()
        self.assertEqual(self.app.text_area(key='review_new_body').value, SOURCE)

    def test_stale_results_model_change_and_undo_never_overwrite_manual_edit(self):
        self.input_body()
        self.generate('style', STYLE, 'みやび文体に変換')
        self.app.text_input(key='ai_pref_model').set_value('another-model').run()
        self.assertTrue(self.button('修正を採用').disabled)
        self.app.text_input(key='ai_pref_model').set_value('gpt-4.1-mini').run()
        self.button('修正を採用').click().run()
        self.input_body('手で追加した文章')
        self.assertTrue(self.button('修正を採用').disabled)
        self.button('元に戻す').click().run(); self.clean()
        self.assertEqual(self.app.text_area(key='review_new_body').value, '手で追加した文章')
        self.assertTrue(any('手動編集' in e.value for e in self.app.error))

    def test_nonmatching_and_evidence_required_suggestions_are_not_auto_applied(self):
        self.page('AI文章校正'); self.input_body()
        data = {'issues': [PROOF['issues'][0] | {'before': '存在しない原文'},
                           PROOF['issues'][1] | {'requires_source': True}, PROOF['issues'][1]]}
        self.generate('proof', data, '10項目でAI校正する')
        self.assertTrue(self.app.button(key='review_new_issue_1_0').disabled)
        self.assertTrue(self.app.button(key='review_new_issue_1_1').disabled)
        self.assertFalse(self.app.button(key='review_new_issue_1_2').disabled)
        self.assertEqual(self.app.text_area(key='review_new_body').value, SOURCE)

    def test_local_duplicate_check_without_key_excludes_self_and_never_calls_api(self):
        sentence = '家族との会話を大切にしながら、ゆっくりと一日を過ごしています。'
        current_id = self.store.save(empty_article() | {'title': '今回の記事', 'body': sentence + '\n' + sentence})
        other_id = self.store.save(empty_article() | {'title': '過去の記事', 'body': sentence})
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}), patch('miyabi.ai_client.generate') as api:
            self.page('重複チェック')
            self.app.selectbox(key='review_target').set_value(str(current_id)).run()
            self.button('ローカルで重複を確認').click().run(); self.clean()
            result = self.app.session_state['review_spaces'][str(current_id)]['local']['data']
            self.assertTrue(result['internal'])
            self.assertEqual([row['id'] for row in result['past']], [other_id])
            self.assertEqual(self.store.get(current_id)['body'], sentence + '\n' + sentence)
            self.input_body('別の文章に変更しました。', str(current_id))
            self.assertTrue(any('前回の結果' in w.value for w in self.app.warning))
            api.assert_not_called()

    def test_only_selected_past_excerpt_is_sent_and_consent_invalidates_on_change(self):
        picked = self.store.save(empty_article() | {'title': '選んだ記事', 'body': '家族との時間を大切にします。', 'notes': '送信禁止の備考'})
        unpicked = self.store.save(empty_article() | {'title': '選ばない記事', 'body': '送信禁止の未選択本文'})
        self.page('重複チェック'); self.input_body()
        self.app.multiselect(key='review_new_reference_ids').set_value([str(picked)]).run()
        request = self.generate('duplicate', {'findings': []}, '選んだ記事とAI比較する')
        self.assertIn('家族との時間を大切にします', request.input_json)
        self.assertNotIn('送信禁止', request.input_json)
        self.assertNotIn(str(unpicked) + '"', request.input_json)
        self.preview()
        self.app.text_area(key=f'review_new_reference_{picked}').set_value('抜粋を変更しました。').run()
        self.assertFalse(any(b.label == '選んだ記事とAI比較する' for b in self.app.button))
        self.assertTrue(any('以前の結果' in w.value for w in self.app.warning))

    def test_review_state_survives_pages_and_reload_is_explicit(self):
        i = self.store.save(empty_article() | {'title': '元の記事', 'body': SOURCE})
        self.app.run(); self.app.selectbox(key='review_target').set_value(str(i)).run()
        self.input_body('校正中の変更', str(i))
        self.page('AI文章校正')
        self.assertEqual(self.app.text_area(key=f'review_{i}_body').value, '校正中の変更')
        self.page('ホーム'); self.page('みやび文体変換')
        self.assertEqual(self.app.text_area(key=f'review_{i}_body').value, '校正中の変更')
        self.assertTrue(self.button('編集内容を読み込み直す').disabled)
        self.checkbox('作業内容を破棄して読み込み直します').check().run()
        self.button('編集内容を読み込み直す').click().run(); self.clean()
        self.assertEqual(self.app.text_area(key=f'review_{i}_body').value, SOURCE)

    def test_failure_keeps_output_and_does_not_expose_remote_error(self):
        self.input_body()
        self.generate('style', STYLE, 'みやび文体に変換')
        self.preview()
        with patch('miyabi.ai_client.generate', side_effect=GenerationError('接続できませんでした')):
            self.button('みやび文体に変換').click().run()
        self.clean()
        self.assertEqual(self.app.text_area(key='review_new_style_candidate').value, STYLE['converted'])
        self.assertEqual(self.app.text_area(key='review_new_body').value, SOURCE)
        self.assertTrue(self.app.error)
        self.app.run()
        self.button('送信内容を確認').click().run()
        self.assertFalse(self.checkbox('送信内容と料金発生を確認しました').value)

    def test_article_metadata_and_other_session_updates_are_protected(self):
        i = self.store.save(empty_article() | {'title': '元のタイトル', 'body': SOURCE, 'notes': '非公開メモ', 'status': '完成', 'hashtags': '#暮らし'})
        self.app.run(); self.app.selectbox(key='review_target').set_value(str(i)).run()
        self.input_body('採用する本文', str(i))
        self.checkbox('選択した記事の編集欄の本文に反映します').check().run()
        self.button('本文を記事編集へ反映').click().run(); self.clean()
        self.button('記事を保存').click().run(); self.clean()
        saved = self.store.get(i)
        self.assertEqual(saved['title'], '元のタイトル')
        self.assertEqual(saved['notes'], '非公開メモ')
        self.assertEqual(saved['status'], '完成')
        self.assertEqual(saved['hashtags'], '#暮らし')
        self.assertEqual(saved['body'], '採用する本文')
        self.page('みやび文体変換')
        self.input_body('さらに校正した本文', str(i))
        self.store.save(saved | {'body': '別セッションの更新'}, i)
        self.checkbox('選択した記事の編集欄の本文に反映します').check().run()
        self.button('本文を記事編集へ反映').click().run(); self.clean()
        self.button('記事を保存').click().run(); self.clean()
        self.assertTrue(self.app.error)
        self.assertEqual(self.store.get(i)['body'], '別セッションの更新')

    def test_editor_changes_after_review_started_are_not_silently_lost(self):
        self.input_body('校正中の本文')
        self.page('記事を書く・編集する')
        self.app.text_area(key='edit_new_body').set_value('編集画面の新しい本文').run()
        self.page('みやび文体変換')
        self.checkbox('選択した記事の編集欄の本文に反映します').check().run()
        self.button('本文を記事編集へ反映').click().run(); self.clean()
        self.assertTrue(any('編集画面の本文' in e.value for e in self.app.error))
        self.assertEqual(self.app.session_state['drafts']['new']['values']['body'], '編集画面の新しい本文')
        self.assertEqual(self.app.text_area(key='review_new_body').value, '校正中の本文')

    def test_deleted_source_keeps_review_text_available_for_export(self):
        i = self.store.save(empty_article() | {'title': '削除される記事', 'body': SOURCE})
        self.app.run(); self.app.selectbox(key='review_target').set_value(str(i)).run()
        self.input_body('退避が必要な校正本文', str(i))
        saved = self.store.get(i); self.store.delete(i, saved['updated_at'])
        self.app.run(); self.clean()
        self.assertEqual(self.app.text_area(key=f'review_{i}_body').value, '退避が必要な校正本文')
        self.checkbox('選択した記事の編集欄の本文に反映します').check().run()
        self.button('本文を記事編集へ反映').click().run(); self.clean()
        self.assertTrue(any('削除' in e.value for e in self.app.error))
        self.assertEqual(self.store.list(), [])

    def test_empty_proof_is_a_reference_result_and_health_warning_is_visible(self):
        self.page('AI文章校正'); self.input_body()
        self.app.selectbox(key='review_new_genre').set_value('健康と美容').run()
        self.assertTrue(any('健康' in w.value for w in self.app.warning))
        self.generate('proof', {'issues': []}, '10項目でAI校正する')
        self.assertTrue(any('指摘はありません' in info.value for info in self.app.info))
        self.assertFalse(any(b.label == 'この修正を採用' for b in self.app.button))


if __name__ == '__main__':
    unittest.main()
