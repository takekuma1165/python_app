import copy
import unittest

from miyabi.review import ReviewError, accept_issue, issue_span, local_duplicates, normalize, patched_body
from review_fixtures import SOURCE, ISSUES


class PatchTests(unittest.TestCase):
    def test_only_selected_occurrence_changes_even_after_lengths_change(self):
        second, accepted = accept_issue(SOURCE, SOURCE, ISSUES, [], 1)
        self.assertEqual(second, SOURCE.rsplit('行きましした', 1)[0] + '行きました。')
        self.assertIn('行きましした', second)
        both, accepted = accept_issue(SOURCE, second, ISSUES, accepted, 0)
        self.assertEqual(both.count('行きました'), 2)
        self.assertNotIn('行きましした', both)
        self.assertEqual(patched_body(SOURCE, ISSUES, [0, 1]), both)

    def test_overlapping_and_duplicate_corrections_are_blocked(self):
        body, accepted = accept_issue(SOURCE, SOURCE, ISSUES, [], 0)
        with self.assertRaisesRegex(ReviewError, '重なって'):
            accept_issue(SOURCE, body, ISSUES, accepted, 2)
        with self.assertRaisesRegex(ReviewError, '採用して'):
            accept_issue(SOURCE, body, ISSUES, accepted, 0)

    def test_manual_edit_and_nonmatching_quote_never_modify_text(self):
        with self.assertRaisesRegex(ReviewError, '本文が変わり'):
            accept_issue(SOURCE, SOURCE + '手動追記', ISSUES, [], 0)
        for change in ({'before': '存在しない文'}, {'occurrence': 3}):
            with self.subTest(change=change), self.assertRaisesRegex(ReviewError, '一致しません'):
                issue_span(SOURCE, ISSUES[0] | change)

    def test_delete_and_evidence_flags(self):
        shortened, _ = accept_issue(SOURCE, SOURCE, ISSUES, [], 2)
        self.assertEqual(shortened.count('今日は公園に'), 1)
        for change in ({'requires_source': True}, {'category': '根拠が必要な記述'}):
            with self.subTest(change=change), self.assertRaisesRegex(ReviewError, '根拠'):
                accept_issue(SOURCE, SOURCE, [ISSUES[0] | change], [], 0)

    def test_emoji_and_multiline_offsets_remain_exact(self):
        source = '🌷はじめに\nゆっくり、ゆっくり。\n🌷はじめに'
        issue = ISSUES[0] | {'before': '🌷はじめに', 'after': '🌸こんにちは', 'occurrence': 2}
        result, _ = accept_issue(source, source, [issue], [], 0)
        self.assertTrue(result.startswith('🌷はじめに\n'))
        self.assertTrue(result.endswith('🌸こんにちは'))


class DuplicateTests(unittest.TestCase):
    def article(self, i, body, title='過去の記事'):
        return {'id': i, 'title': title, 'body': body}

    def test_internal_repetition_and_excluding_current_article(self):
        sentence = '家族との会話を大切にして、ゆっくり一日を過ごしています。'
        result = local_duplicates(sentence + '\n' + sentence, [self.article(1, sentence), self.article(2, sentence)], exclude_id='1')
        self.assertTrue(result['internal'])
        self.assertEqual(result['internal'][0]['score'], 1)
        self.assertEqual([r['id'] for r in result['past']], [2])
        self.assertEqual(result['checked_articles'], 1)

    def test_nfkc_whitespace_and_punctuation_do_not_hide_repeated_text(self):
        a = '２０２６年、家族と過ごす時間を大切にしています。'
        b = '2026年 家族と過ごす時間を大切にしています'
        self.assertEqual(normalize(a), normalize(b))
        result = local_duplicates(a, [self.article(1, b)])
        self.assertEqual(result['past'][0]['score'], 1)

    def test_unrelated_text_and_empty_articles_do_not_match(self):
        result = local_duplicates('家族との会話を大切にして、ゆっくり一日を過ごしています。',
                                  [self.article(1, '銀河系の観測データから恒星の寿命を計算する手法を研究します。'), self.article(2, '')])
        self.assertFalse(result['past'])
        self.assertFalse(result['internal'])
        self.assertEqual(result['checked_articles'], 1)

    def test_paragraph_overlap_is_detected_in_otherwise_different_articles(self):
        same = '朝に窓を開けて、深呼吸をしながら体をゆっくり伸ばしています。'
        current = same + '\n予定を詰め込みすぎず暮らしの余白をつくります。'
        past = '仕事道具の整理整頓について考えています。\n' + same
        result = local_duplicates(current, [self.article(3, past)])
        self.assertTrue(result['past'])
        self.assertEqual(result['past'][0]['excerpt'], same)

    def test_limits_and_top_results_are_reported(self):
        text = '\n'.join('家族との会話を大切にしながら一日を過ごしています。' for _ in range(302))
        result = local_duplicates(text, [self.article(1, 'あ' * 100001), self.article(2, text)])
        self.assertEqual(result['units_total'], 302)
        self.assertEqual(result['units_checked'], 300)
        self.assertEqual(result['skipped_articles'], [1])
        self.assertEqual(result['limited_articles'], [2])
        self.assertEqual(len(result['internal']), 20)
        with self.assertRaises(ReviewError): local_duplicates('あ' * 100001, [])
        with self.assertRaises(ReviewError): local_duplicates('  ', [])


if __name__ == '__main__':
    unittest.main()
