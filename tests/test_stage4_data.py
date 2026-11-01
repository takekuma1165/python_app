import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from miyabi.backup import backup_bytes, encode_backup, fingerprint, restore_backup, snapshot, validate_backup
from miyabi.dashboard import summarize, recommend
from miyabi.database import ArticleStore, ConflictError, empty_article
from miyabi.publication import empty_pack, validate_pack
from miyabi.settings import DEFAULT_SETTINGS, move_data_folder, resolve_data_dir


class Stage4DataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = ArticleStore(self.root / 'original' / 'miyabi.sqlite3')
        self.i = self.store.save(empty_article() | {'title': '元の記事', 'body': '大切な文章', 'notes': '本人だけの備考'})
        self.article = self.store.get(self.i)

    def seed_pack_and_settings(self):
        values = empty_pack(self.article) | {'introduction': '紹介文', 'thread_1': '告知文'}
        self.store.save_publication(self.i, values, self.article['updated_at'], None)
        self.store.save_settings(DEFAULT_SETTINGS | {'tone': '落ち着いた温かい文章'}, None)
        return values

    def test_publication_persists_independently_and_checks_both_versions(self):
        values = self.seed_pack_and_settings()
        reopened = ArticleStore(self.store.path)
        stored = reopened.publication(self.i)
        self.assertEqual(stored['data'], values)
        self.assertEqual(reopened.get(self.i)['body'], '大切な文章')
        with self.assertRaises(ConflictError): self.store.save_publication(self.i, values, self.article['updated_at'], None)
        self.store.save(self.article | {'body': '他画面からの変更'}, self.i)
        with self.assertRaises(ConflictError): self.store.save_publication(self.i, values, self.article['updated_at'], stored['updated_at'])
        self.assertEqual(self.store.publication(self.i)['data'], values)

    def test_deleting_article_cascades_publication_but_duplicate_does_not_copy_promotion(self):
        self.seed_pack_and_settings()
        duplicate = self.store.duplicate(self.i)
        self.assertIsNone(self.store.publication(duplicate))
        self.store.delete(self.i, self.article['updated_at'])
        self.assertIsNone(self.store.publication(self.i))
        self.assertIsNotNone(self.store.get(duplicate))

    def test_settings_validate_and_do_not_silently_overwrite_another_session(self):
        version = self.store.save_settings(DEFAULT_SETTINGS, None)
        with self.assertRaises(ConflictError): self.store.save_settings(DEFAULT_SETTINGS, None)
        for change in ({'word_count': 10}, {'model': ''}, {'ai_enabled': 'true'}, {'unexpected': 'secret'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.store.save_settings(DEFAULT_SETTINGS | change, version)
        self.assertEqual(self.store.settings()[1], version)

    def test_backup_roundtrip_restores_every_saved_category_and_saves_previous_data(self):
        pack = self.seed_pack_and_settings()
        raw = backup_bytes(self.store)
        data = validate_backup(raw)
        self.assertEqual(data['articles'][0]['notes'], '本人だけの備考')
        self.assertNotIn('OPENAI_API_KEY', raw.decode())
        other = self.store.save(empty_article() | {'title': '復元前の記事'})
        safety = restore_backup(self.store, raw, fingerprint(snapshot(self.store)))
        self.assertTrue(safety.exists())
        self.assertEqual(len(validate_backup(safety.read_bytes())['articles']), 2)
        self.assertIsNone(self.store.get(other))
        restored = self.store.get(self.i)
        for key in ('title', 'body', 'notes', 'created_at'):
            self.assertEqual(restored[key], self.article[key])
        self.assertNotEqual(restored['updated_at'], self.article['updated_at'])
        self.assertEqual(self.store.publication(self.i)['data'], pack)
        self.assertEqual(self.store.publication(self.i)['source_updated_at'], restored['updated_at'])
        self.assertEqual(self.store.settings()[0]['tone'], '落ち着いた温かい文章')
        with self.assertRaises(ConflictError): self.store.save(self.article, self.i, self.article['updated_at'])

    def test_restore_can_restore_an_empty_database(self):
        with tempfile.TemporaryDirectory() as directory:
            empty = ArticleStore(Path(directory) / 'db.sqlite3')
            raw = backup_bytes(empty)
        restore_backup(self.store, raw, fingerprint(snapshot(self.store)))
        self.assertEqual(self.store.list(), [])
        self.assertIsNone(self.store.settings()[1])

    def test_corrupt_unknown_and_inconsistent_backup_never_touch_live_data(self):
        self.seed_pack_and_settings()
        before = snapshot(self.store)
        invalid = [b'not JSON', json.dumps({'format': 'unknown'}).encode()]
        for mutation in ('status', 'duplicate_id', 'foreign_pack', 'unknown_setting', 'date'):
            payload = copy.deepcopy(before)
            if mutation == 'status': payload['articles'][0]['status'] = '未知'
            if mutation == 'duplicate_id': payload['articles'].append(copy.deepcopy(payload['articles'][0]))
            if mutation == 'foreign_pack': payload['publications'][0]['article_id'] = 999
            if mutation == 'unknown_setting': payload['settings']['data']['api_key'] = 'should-not-be-imported'
            if mutation == 'date': payload['articles'][0]['created_at'] = 'not a date'
            invalid.append(encode_backup(payload))
        for raw in invalid:
            with self.subTest(raw=raw[:30]), self.assertRaises(ValueError):
                restore_backup(self.store, raw, fingerprint(before))
            self.assertEqual(snapshot(self.store), before)

    def test_restore_refuses_changes_after_preview(self):
        raw = backup_bytes(self.store); expected = fingerprint(snapshot(self.store))
        self.store.save(self.article | {'body': '確認後の変更'}, self.i)
        with self.assertRaisesRegex(ValueError, '変更'):
            restore_backup(self.store, raw, expected)
        self.assertEqual(self.store.get(self.i)['body'], '確認後の変更')

    def test_restore_rolls_back_on_write_failure_and_backup_failure(self):
        raw = backup_bytes(self.store)
        before = snapshot(self.store)
        with self.store.connection() as conn:
            conn.execute("CREATE TRIGGER fail_restore BEFORE INSERT ON articles BEGIN SELECT RAISE(ABORT,'test-only'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            restore_backup(self.store, raw, fingerprint(before))
        self.assertEqual(snapshot(self.store), before)
        with patch('pathlib.Path.open', side_effect=PermissionError('no write')):
            with self.assertRaises(PermissionError): restore_backup(self.store, raw, fingerprint(before))
        self.assertEqual(snapshot(self.store), before)

    def test_storage_copy_preserves_original_and_never_overwrites_existing_destination(self):
        self.seed_pack_and_settings()
        pointer = self.root / 'local_config.json'
        with patch.dict(os.environ, {'MIYABI_DATA_DIR': '', 'MIYABI_CONFIG_PATH': str(pointer)}):
            destination = move_data_folder(self.store, self.root, '新しい保存先')
            self.assertEqual(resolve_data_dir(self.root), destination.parent)
            self.assertEqual(snapshot(ArticleStore(destination)), snapshot(self.store))
            with self.assertRaises(FileExistsError): move_data_folder(self.store, self.root, '新しい保存先')
            self.assertTrue(self.store.path.exists())
        with patch.dict(os.environ, {'MIYABI_DATA_DIR': str(self.root / 'forced')}):
            self.assertEqual(resolve_data_dir(self.root), self.root / 'forced')
            with self.assertRaises(ValueError): move_data_folder(self.store, self.root, 'blocked')

    def test_dashboard_month_is_japan_time_and_statuses_are_separate(self):
        records = [self.article | {'status': '完成', 'created_at': '2026-10-31T16:00:00+00:00'},
                   self.article | {'status': '公開済み', 'created_at': '2026-10-31T14:00:00+00:00'}]
        stats = summarize(records, datetime(2026, 11, 1, tzinfo=timezone.utc))
        self.assertEqual(stats['monthly'], 1)
        self.assertEqual(stats['complete'], 1); self.assertEqual(stats['published'], 1)
        self.assertEqual(stats['in_progress'], 0)
        self.assertEqual(summarize([])['progress'], 0)
        suggestions = recommend([])
        self.assertEqual(len(suggestions), 3)
        self.assertNotIn(suggestions[0]['title'], [r['title'] for r in recommend([self.article | {'title': suggestions[0]['title']}])])

    def test_old_article_only_database_is_upgraded_without_rewriting_articles(self):
        original = self.store.get(self.i)
        with self.store.connection() as conn:
            conn.execute('DROP TABLE publication_packs')
            conn.execute('DROP TABLE app_settings')
        upgraded = ArticleStore(self.store.path)
        self.assertEqual(upgraded.get(self.i), original)
        self.assertIsNone(upgraded.publication(self.i))
        self.assertIsNone(upgraded.settings()[1])
        upgraded.save_publication(self.i, empty_pack(original), original['updated_at'], None)
        self.assertIsNotNone(upgraded.publication(self.i))

    def test_pack_limits_prevent_unusable_threads_and_tag_lists(self):
        for change in ({'thread_1': 'あ' * 501}, {'hashtags': ' '.join(f'#tag{i}' for i in range(9))}, {'title': ''}):
            with self.assertRaises(ValueError): validate_pack(empty_pack(self.article) | change)


if __name__ == '__main__': unittest.main()
