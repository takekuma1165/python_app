import copy
import unittest
import test_review_client as sdk_helpers
from miyabi.ai_client import GenerationError, SCHEMAS, prepare_request, validate_result
from publication_fixtures import PUBLICATION


class PublicationClientTests(unittest.TestCase):
    def test_payload_only_includes_selected_article_material(self):
        values = {'title': '小さな工夫', 'body': '毎日少しずつ工夫しています。', 'genre': '暮らしを整える', 'audience': '50代', 'tone': '温かく',
                  'notes': '秘密の備考', 'other_article': '選ばない本文'}
        request = prepare_request('publication', values, 'gpt-4.1-mini')
        self.assertIn('小さな工夫', request.input_json)
        self.assertNotIn('秘密', request.input_json)
        self.assertNotIn('選ばない本文', request.input_json)
        validate_result(PUBLICATION, SCHEMAS['publication'])

    def test_real_sdk_serializes_publication_and_rejects_duplicate_hashtags(self):
        values = {'title': '小さな工夫', 'body': '毎日の工夫を振り返りました。', 'genre': '暮らしを整える', 'audience': '50代', 'tone': '温かく'}
        self.assertEqual(sdk_helpers.ReviewClientTests().sdk_response('publication', PUBLICATION, values), PUBLICATION)
        with self.assertRaisesRegex(GenerationError, '重複'):
            sdk_helpers.ReviewClientTests().sdk_response('publication', PUBLICATION | {'hashtags': ['#同じ'] * 5}, values)

    def test_promotional_counts_lengths_and_hash_format_are_validated(self):
        for change in ({'hashtags': ['#暮らし']}, {'threads': ['一つだけ']}, {'threads': ['あ' * 501] * 3},
                       {'cover': 'あ' * 31}, {'hashtags': ['#暮らし', '#one', '#two', '#three', 'bad tag']}):
            with self.subTest(change=change), self.assertRaises(GenerationError):
                validate_result(PUBLICATION | change, SCHEMAS['publication'])
        with self.assertRaises(GenerationError): prepare_request('publication', {'title': '', 'body': '本文'}, 'gpt-4.1-mini')


if __name__ == '__main__': unittest.main()
