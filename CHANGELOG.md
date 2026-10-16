# Changelog

## Unreleased — 2026-10-16

- Preserve ordinary Python traceback frames as a complete block when they fit the remaining source-line budget, before adding unrelated tail output.
- Keep the hard line budget and recent-error priority when a block cannot fit. Exception groups and prefixed traceback formats remain unsupported.
- Added traceback retention and small-budget regression tests; 15 tests pass locally on Python 3.13.

## Unreleased — 2026-10-15

- Fix credential masking for quoted JSON/dictionary keys (token, api_key, password and secret), including escaped quotes in values.
- Add regression tests for quoted keys and escaped values. Local Python 3.13: 13 tests passed.

## Unreleased — 2026-10-14

- Fix Python exception headers such as ValueError, TypeError and qualified custom errors being omitted from small-budget summaries.
- Add regression coverage for five exception classes and avoid matching exception names in ordinary prose.
- Local Python 3.13 validation: 10 tests passed.

## 0.1.0 — 2026-10-14

- Added file/stdin input, text/JSON output, original line numbers and omission markers.
- Added recent-error prioritization, surrounding context, adjacent-repeat folding and common credential masking.
- Added CLI input validation and 8 passing local tests on Python 3.13.
- Added Windows/Linux CI configuration; remote CI has not run yet.
- First public source release. Maintenance begins 2026-10-14 (Asia/Shanghai).
