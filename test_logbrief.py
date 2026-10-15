import json
import subprocess
import sys
import unittest
from pathlib import Path
from logbrief import clean, render, summarize


class LogBriefTests(unittest.TestCase):
    def test_json_secret_keys_are_redacted(self):
        for key in ['token', 'api_key', 'password', 'secret']:
            with self.subTest(key=key):
                payload = json.dumps({key: 'private value', 'message': 'keep this'})
                result = clean(payload)
                self.assertNotIn('private value', result)
                self.assertIn('keep this', result)

    def test_single_quoted_secret_key(self):
        self.assertNotIn('private value', clean("{'token': 'private value'}"))

    def test_json_escaped_secret_is_fully_redacted(self):
        payload = json.dumps({'token': 'prefix "hidden" suffix'})
        result = clean(payload)
        self.assertNotIn('hidden', result)
        self.assertNotIn('suffix', result)


    def test_python_exception_survives_long_traceback(self):
        for exception in ['ValueError', 'TypeError', 'RuntimeError', 'custom.ParseError', 'custom.ServiceException']:
            with self.subTest(exception=exception):
                text = '\n'.join(['Traceback (most recent call last):'] + ['  frame details'] * 10 + [exception + ': broken'] + ['cleanup complete'] * 10)
                result = summarize(text, 1, 0)
                self.assertEqual(result['entries'][0]['text'], exception + ': broken')

    def test_exception_words_in_prose_are_not_error_headers(self):
        result = summarize('Documentation for ValueError\nall done', 1, 0)
        self.assertEqual(result['error_lines'], 0)

    def test_failure_survives_noise(self):
        data = '\n'.join(['noise'] * 200 + ['fatal: compile failed', 'source.c:12'] + ['noise'] * 200)
        result = summarize(data, 5, 1)
        self.assertIn('fatal: compile failed', render(result))
        self.assertIn('source.c:12', render(result))
        self.assertEqual(result['selected_lines'], 5)

    def test_recent_errors_win_small_budget(self):
        result = summarize('error: old\nnoise\nerror: new', 1)
        self.assertEqual(result['entries'][0]['text'], 'error: new')

    def test_repeated_lines_and_positions(self):
        result = summarize('ok\nok\nok')
        self.assertEqual(result['entries'][0]['repeat'], 3)
        self.assertIn('[1-3 x3]', render(result))

    def test_redaction(self):
        value = clean('token="two words" password=abc Bearer abcdef https://me:pass@example.com \x1b[31mERROR\x1b[0m')
        for secret in ['two words', 'abc', 'abcdef', 'me:pass', '\x1b']:
            self.assertNotIn(secret, value)
        self.assertIn('ERROR', value)

    def test_empty(self):
        self.assertEqual(summarize('')['selected_lines'], 0)

    def test_invalid_budget(self):
        with self.assertRaises(ValueError):
            summarize('x', 0)

    def test_stdin_json(self):
        process = subprocess.run([sys.executable, str(Path(__file__).with_name('logbrief.py')), '--json'], input='error: broken\n', text=True, capture_output=True)
        self.assertEqual(process.returncode, 0)
        self.assertEqual(json.loads(process.stdout)['error_lines'], 1)

    def test_cli_bad_budget(self):
        process = subprocess.run([sys.executable, str(Path(__file__).with_name('logbrief.py')), '--max-lines', '0'], capture_output=True)
        self.assertEqual(process.returncode, 2)


if __name__ == '__main__':
    unittest.main()
