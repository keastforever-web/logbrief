import json
import subprocess
import sys
import unittest
from pathlib import Path
from logbrief import clean, render, summarize


class LogBriefTests(unittest.TestCase):
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
