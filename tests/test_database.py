import sqlite3
import tempfile
import unittest
from pathlib import Path

from miyabi.database import ArticleStore, ConflictError, FIELDS, empty_article
from miyabi.export import article_markdown, article_text, download_name


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "日本語フォルダー" / "test.sqlite3"
        self.store = ArticleStore(self.path)

    def article(self, **values):
        return empty_article() | {"title": "私らしい暮らし", "body": "## 最初の一歩\n\n経験を大切に。"} | values

    def test_create_edit_and_reopen_all_fields(self):
        a = self.article(keyword="暮らし", search_intent="片付けたい", outline="## 構成",
                         hashtags="#暮らし", published_on="2026-10-27", note_url="https://note.com/miyabi/n/test", notes="私的メモ")
        i = self.store.save(a)
        saved = self.store.get(i)
        self.assertTrue(saved["created_at"])
        self.assertEqual(set(FIELDS) - saved.keys(), set())
        for field in FIELDS:
            self.assertEqual(a[field], saved[field])
        self.store.save(a | {"body": "編集済み", "status": "完成"}, i, saved["updated_at"])
        reopened = ArticleStore(self.path).get(i)
        self.assertEqual(reopened["body"], "編集済み")
        self.assertEqual(reopened["created_at"], saved["created_at"])
        self.assertNotEqual(reopened["updated_at"], saved["updated_at"])

    def test_validation_and_failed_update_preserve_saved_data(self):
        i = self.store.save(self.article())
        for change in ({"title": "  "}, {"status": "未知"}, {"published_on": "2026-02-30"}, {"note_url": "javascript:bad"}):
            with self.assertRaises(ValueError):
                self.store.save(self.article(**change), i)
            self.assertEqual(self.store.get(i)["title"], "私らしい暮らし")

    def test_concurrent_update_and_delete_do_not_destroy_changes(self):
        i = self.store.save(self.article())
        old = self.store.get(i)
        self.store.save(self.article(body="別画面の更新"), i, old["updated_at"])
        with self.assertRaises(ConflictError):
            self.store.save(self.article(body="上書き"), i, old["updated_at"])
        with self.assertRaises(ConflictError):
            self.store.delete(i, old["updated_at"])
        self.assertEqual(self.store.get(i)["body"], "別画面の更新")

    def test_search_filter_sort_duplicate_and_delete(self):
        first = self.store.save(self.article(title="あ 100%", status="公開済み", note_url="https://note.com/test", published_on="2026-10-27"))
        second = self.store.save(self.article(title="い", keyword="数秘術"))
        self.assertEqual(self.store.list("数秘術")[0]["id"], second)
        self.assertEqual(len(self.store.list("100%")), 1)
        self.assertEqual(len(self.store.list("' OR 1=1 --")), 0)
        self.assertEqual(len(self.store.list(status="公開済み")), 1)
        self.assertEqual(self.store.list(order="作成が古い順")[0]["id"], first)
        copied = self.store.duplicate(first)
        copy = self.store.get(copied)
        self.assertEqual(copy["status"], "アイデア")
        self.assertEqual(copy["note_url"], "")
        self.assertEqual(copy["published_on"], "")
        self.store.delete(copied, copy["updated_at"])
        self.assertIsNone(self.store.get(copied))
        self.assertEqual(len(self.store.list()), 2)

    def test_transaction_rolls_back(self):
        i = self.store.save(self.article())
        with self.assertRaises(sqlite3.IntegrityError):
            with self.store.connection() as conn:
                conn.execute("UPDATE articles SET body='changed' WHERE id=?", (i,))
                conn.execute("UPDATE articles SET status='invalid' WHERE id=?", (i,))
        self.assertEqual(self.store.get(i)["body"], self.article()["body"])

    def test_exports_do_not_include_private_notes(self):
        a = self.article(notes="非公開の備考", outline="非公開の構成", hashtags="#暮らし")
        md = article_markdown(a)
        self.assertTrue(md.startswith("# 私らしい暮らし\n"))
        self.assertIn("#暮らし", md)
        self.assertNotIn("非公開", md)
        self.assertNotIn("## 最初", article_text(a))
        self.assertNotIn("/", download_name('CON:/a', 'md'))
        self.assertTrue(download_name("CON", "md").startswith("miyabi_"))


if __name__ == "__main__":
    unittest.main()
