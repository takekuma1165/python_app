import copy
import json
import os
import unittest
from unittest.mock import patch

import httpx2
from openai import OpenAI

from miyabi.ai_client import GenerationError, MODES, SYSTEM_PROMPT, generate, prepare_request
from ai_fixtures import RESULTS


BASE = dict(genre="暮らしを整える", audience="50代の女性", problem="始められない", message="小さな一歩から",
            purpose="共感", keyword="暮らし", theme="暮らしを整える", search_intent="小さく始める方法", title="暮らしの一歩",
            outline="## 小さな一歩", word_count=2000, revision="", mode=MODES[0], section="## 一歩",
            existing_body="元の本文", memo="・引き出しを整理した", experience="引き出しを片付けた",
            experience_problem="物が見つからない", experience_thought="小さく始めよう", experience_tried="一つだけ整理した",
            experience_message="無理なく", notes="送信してはいけない備考", body="無関係の本文", api_key="送信してはいけないキー")


class AiClientTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {"OPENAI_API_KEY": "test-only-not-a-real-key"})
        env.start()
        self.addCleanup(env.stop)

    def call_with_transport(self, request, handler):
        """Exercise the real SDK serialization and error mapping, without network."""
        def factory(**kwargs):
            self.assertEqual(kwargs['base_url'], 'https://api.openai.com/v1')
            self.assertEqual(kwargs['max_retries'], 0)
            self.assertEqual(kwargs['timeout'], 60.0)
            return OpenAI(**kwargs, http_client=httpx2.Client(transport=httpx2.MockTransport(handler)))
        with patch('miyabi.ai_client.OpenAI', side_effect=factory):
            return generate(request)

    def response(self, data, status='completed'):
        return {"id": "resp_test", "created_at": 0, "model": "gpt-4.1-mini", "object": "response", "status": status,
                "output": [{"id": "msg_test", "type": "message", "role": "assistant", "status": "completed",
                            "content": [{"type": "output_text", "text": json.dumps(data, ensure_ascii=False), "annotations": []}]}]}

    def test_all_four_requests_use_actual_sdk_and_validate_output(self):
        for kind, result in RESULTS.items():
            with self.subTest(kind=kind):
                request = prepare_request(kind, BASE, 'gpt-4.1-mini')
                seen = []
                def handler(http_request):
                    self.assertEqual(str(http_request.url), 'https://api.openai.com/v1/responses')
                    payload = json.loads(http_request.content)
                    self.assertFalse(payload['store'])
                    self.assertTrue(payload['text']['format']['strict'])
                    self.assertEqual(payload, request.payload())
                    self.assertNotIn('送信してはいけない', payload['input'])
                    seen.append(payload)
                    return httpx2.Response(200, json=self.response(result))
                self.assertEqual(self.call_with_transport(request, handler), result)
                self.assertEqual(len(seen), 1)

    def test_modes_send_only_needed_material_and_facts(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                request = prepare_request('body', BASE | {'mode': mode}, 'gpt-4.1-mini')
                material = json.loads(request.input_json)['material']
                self.assertEqual(material['experience'], '引き出しを片付けた')
                self.assertEqual('existing_body' in material, mode == MODES[4])
                self.assertEqual('memo' in material, mode == MODES[5])
                self.assertEqual('section' in material, mode == MODES[2])
        self.assertIn('事実を付け足しません', SYSTEM_PROMPT)
        self.assertIn('未検証', SYSTEM_PROMPT)

    def test_input_validation_and_fingerprint(self):
        for kind, update in [('themes', {'problem': ''}), ('titles', {'theme': ''}), ('body', {'title': ''}),
                             ('body', {'word_count': 9000}), ('body', {'mode': MODES[2], 'section': ''}),
                             ('body', {'mode': MODES[4], 'existing_body': ''}), ('body', {'mode': MODES[5], 'memo': ''}),
                             ('outline', {'revision': 'H2だけ修正', 'outline': ''})]:
            with self.subTest(kind=kind, update=update), self.assertRaises(GenerationError):
                prepare_request(kind, BASE | update, 'gpt-4.1-mini')
        with self.assertRaises(GenerationError):
            prepare_request('themes', BASE | {'problem': 'あ' * 40001}, 'gpt-4.1-mini')
        first = prepare_request('themes', BASE, 'gpt-4.1-mini')
        self.assertNotEqual(first.fingerprint, prepare_request('themes', BASE | {'problem': '別の悩み'}, 'gpt-4.1-mini').fingerprint)
        self.assertNotEqual(first.fingerprint, prepare_request('themes', BASE, 'another-model').fingerprint)
        self.assertNotIn('outline', json.loads(prepare_request('outline', BASE, 'gpt-4.1-mini').input_json)['material'])
        partial = prepare_request('outline', BASE | {'revision': 'H2だけ修正'}, 'gpt-4.1-mini')
        self.assertEqual(json.loads(partial.input_json)['material']['outline'], BASE['outline'])

    def test_missing_key_does_not_create_client(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}), patch('miyabi.ai_client.OpenAI') as client:
            with self.assertRaisesRegex(GenerationError, '未設定'):
                generate(prepare_request('themes', BASE, 'gpt-4.1-mini'))
            client.assert_not_called()

    def test_http_errors_are_japanese_without_remote_details_and_never_retry(self):
        request = prepare_request('themes', BASE, 'gpt-4.1-mini')
        for code, expected in ((401, 'APIキー'), (403, '権限'), (429, '上限'), (400, '対応'), (500, 'OpenAI側')):
            calls = []
            def handler(http_request):
                calls.append(http_request)
                return httpx2.Response(code, json={'error': {'message': 'private-input secret-key must-not-display', 'type': 'test'}})
            with self.subTest(code=code), self.assertRaises(GenerationError) as error:
                self.call_with_transport(request, handler)
            self.assertIn(expected, str(error.exception))
            self.assertNotIn('must-not-display', str(error.exception))
            self.assertEqual(len(calls), 1)

    def test_timeout_and_connection_errors_do_not_retry(self):
        for exc, expected in ((httpx2.ReadTimeout, '時間内'), (httpx2.ConnectError, '接続')):
            calls = []
            def handler(request):
                calls.append(request)
                raise exc('private-transport-details', request=request)
            with self.subTest(exc=exc), self.assertRaises(GenerationError) as error:
                self.call_with_transport(prepare_request('themes', BASE, 'gpt-4.1-mini'), handler)
            self.assertIn(expected, str(error.exception))
            self.assertNotIn('private-transport-details', str(error.exception))
            self.assertEqual(len(calls), 1)

    def test_malformed_incomplete_empty_and_refused_answers_are_rejected(self):
        bad_count = copy.deepcopy(RESULTS['themes']); bad_count['themes'].pop()
        invalid = [self.response({'themes': []}), self.response(bad_count), self.response({'other': 'wrong'}),
                   self.response(RESULTS['themes'], status='incomplete'), self.response(RESULTS['themes'])]
        invalid[-1]['output'][0]['content'] = [{'type': 'output_text', 'text': 'not json', 'annotations': []}]
        refusal = self.response(RESULTS['themes'])
        refusal['output'][0]['content'] = [{'type': 'refusal', 'refusal': 'private refusal'}]
        invalid.append(refusal)
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(GenerationError):
                self.call_with_transport(prepare_request('themes', BASE, 'gpt-4.1-mini'),
                                         lambda request: httpx2.Response(200, json=payload))


if __name__ == '__main__':
    unittest.main()
