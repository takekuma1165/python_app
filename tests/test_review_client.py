import copy
import json
import os
import unittest
from unittest.mock import patch

import httpx2
from openai import OpenAI

from miyabi.ai_client import GenerationError, SCHEMAS, generate, prepare_request, validate_result
from miyabi.review import CHECK_CATEGORIES, STYLE_MODES
from review_fixtures import VALUES, STYLE, PROOF, DUPLICATE


class ReviewClientTests(unittest.TestCase):
    def sdk_response(self, kind, data, values=None):
        request = prepare_request(kind, values or VALUES, 'gpt-4.1-mini')
        def handle(http_request):
            payload = json.loads(http_request.content)
            self.assertEqual(payload, request.payload())
            self.assertNotIn('秘密の', payload['input'])
            self.assertNotIn('未選択の記事', payload['input'])
            return httpx2.Response(200, json={
                'id': 'resp_review', 'created_at': 0, 'model': request.model, 'object': 'response', 'status': 'completed',
                'output': [{'id': 'msg_review', 'type': 'message', 'role': 'assistant', 'status': 'completed',
                            'content': [{'type': 'output_text', 'text': json.dumps(data, ensure_ascii=False), 'annotations': []}]}],
            })
        def client(**kwargs):
            return OpenAI(**kwargs, http_client=httpx2.Client(transport=httpx2.MockTransport(handle)))
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-not-real'}), patch('miyabi.ai_client.OpenAI', side_effect=client):
            return generate(request)

    def test_three_review_types_use_real_sdk_with_only_allowed_material(self):
        for kind, data in (('style', STYLE), ('proof', PROOF), ('duplicate', DUPLICATE)):
            with self.subTest(kind=kind):
                self.assertEqual(self.sdk_response(kind, data), data)

    def test_six_styles_and_all_ten_proof_categories(self):
        for mode in STYLE_MODES:
            request = prepare_request('style', VALUES | {'style_mode': mode}, 'gpt-4.1-mini')
            self.assertIn(mode, request.input_json)
        proof = prepare_request('proof', VALUES, 'gpt-4.1-mini')
        for category in CHECK_CATEGORIES:
            self.assertIn(category, proof.input_json)
        self.assertIn('事実', prepare_request('style', VALUES, 'gpt-4.1-mini').input_json)

    def test_proof_types_categories_and_occurrence_are_validated(self):
        for change in ({'occurrence': 0}, {'occurrence': True}, {'requires_source': 'false'}, {'category': '未知の項目'}, {'before': ''}):
            with self.subTest(change=change), self.assertRaises(GenerationError):
                validate_result({'issues': [PROOF['issues'][0] | change]}, SCHEMAS['proof'])
        validate_result({'issues': [PROOF['issues'][0] | {'after': ''}]}, SCHEMAS['proof'])
        validate_result({'issues': []}, SCHEMAS['proof'])

    def test_invalid_reference_quotes_or_ids_are_rejected(self):
        for change in ({'article_id': '999'}, {'past_quote': '創作した引用'}, {'current_quote': '存在しない現在の引用'}):
            data = {'findings': [DUPLICATE['findings'][0] | change]}
            with self.subTest(change=change), self.assertRaisesRegex(GenerationError, '引用'):
                self.sdk_response('duplicate', data)

    def test_empty_input_bad_style_too_many_and_oversized_references(self):
        for kind in ('style', 'proof', 'duplicate'):
            with self.subTest(kind=kind), self.assertRaises(GenerationError):
                prepare_request(kind, VALUES | {'body': ''}, 'gpt-4.1-mini')
        with self.assertRaises(GenerationError): prepare_request('style', VALUES | {'style_mode': 'unknown'}, 'gpt-4.1-mini')
        for refs in ([], VALUES['references'] * 6, [VALUES['references'][0] | {'excerpt': 'あ' * 3001}],
                     VALUES['references'] * 2, [VALUES['references'][0] | {'notes': 'unexpected'}]):
            with self.subTest(refs=refs), self.assertRaises(GenerationError):
                prepare_request('duplicate', VALUES | {'references': refs}, 'gpt-4.1-mini')


if __name__ == '__main__':
    unittest.main()
