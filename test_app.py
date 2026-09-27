import json
import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import app

class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = app.DB
        app.DB = Path(self.temp.name) / 'test.sqlite3'
        self.message = '我是林悦，需要自动整理客户邮件，预算 5000 元，两周内完成。请联系 lin@example.com。'
    def tearDown(self):
        app.DB = self.original
        self.temp.cleanup()
    def payload(self, **changes):
        fields = dict(name='林悦', email='lin@example.com', company='', need='自动整理客户邮件', budget='5000 元', timeline='两周内', category='automation')
        fields.update(changes)
        return {'prepared':app.prepare({'message':self.message}), 'ai':{'message':{'content':json.dumps(fields)}}}
    def test_valid_and_duplicate(self):
        result = app.finalize(self.payload())
        self.assertEqual(result['lead']['status'], 'ready_for_review')
        self.assertFalse(result['duplicate'])
        self.assertTrue(app.prepare({'message':self.message})['duplicate'])
        self.assertEqual(len(app.records()), 1)
    def test_hallucinated_fields_are_removed(self):
        result = app.finalize(self.payload(budget='10000 元', name='王强'))['lead']
        self.assertEqual(result['budget'], '')
        self.assertEqual(result['name'], '')
        self.assertEqual(result['status'], 'needs_info')
        self.assertTrue(result['warnings'])
    def test_ai_failure_preserves_original(self):
        result = app.finalize({'prepared': app.prepare({'message':self.message}), 'ai':{'error':'timeout'}})['lead']
        self.assertEqual(result['ai_status'], 'unavailable')
        self.assertEqual(result['message'], self.message)
        self.assertTrue(result['human_review_required'])
    def test_empty_too_long_and_wrong_type(self):
        for message in ['', 'a'*6001, 123, None, []]:
            self.assertEqual(app.prepare({'message':message})['http_status'], 400)
    def test_ai_failure_can_be_retried_without_new_record(self):
        first = app.finalize({'prepared':app.prepare({'message':self.message}), 'ai':{}})
        self.assertTrue(app.prepare({'message':self.message})['needs_ai'])
        retried = app.finalize(self.payload())
        self.assertEqual(retried['lead']['ai_status'], 'extracted')
        self.assertEqual(retried['lead']['id'], first['lead']['id'])
        self.assertEqual(len(app.records()), 1)
    def test_qwen_structured_json_compatibility(self):
        payload = self.payload()
        payload['ai']['message']['thinking'] = payload['ai']['message'].pop('content')
        result = app.finalize(payload)['lead']
        self.assertEqual(result['ai_status'], 'extracted')
        self.assertNotIn('thinking', result)
    def test_concurrent_finalization_only_inserts_once(self):
        payload = self.payload()
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _:app.finalize(payload), range(4)))
        self.assertEqual(sum(not r['duplicate'] for r in results), 1)
        self.assertEqual(len(app.records()), 1)
    def test_spreadsheet_formula_escaped(self):
        self.message = '=HYPERLINK("example.com") 我需要自动化，请联系 lin@example.com。'
        app.finalize(self.payload(name='=HYPERLINK("example.com")'))
        self.assertIn("'=HYPERLINK", app.csv_text())
    def test_multiple_addresses_require_review(self):
        self.message += '备用地址 other@example.com。'
        result = app.finalize(self.payload())['lead']
        self.assertEqual(result['email'], '')
        self.assertTrue(result['warnings'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
