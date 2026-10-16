# LogBrief

Turn noisy build and test logs into deterministic, line-numbered summaries for humans and coding agents. Runs locally with Python 3.10+ and no runtime dependencies or API keys.

## Quick start

```sh
python logbrief.py build.log --max-lines 80 --context 2
python logbrief.py build.log --json
```

Pipe input on Unix or PowerShell:

```sh
python logbrief.py < build.log
```

```powershell
Get-Content build.log | python logbrief.py --max-lines 30
```

Optional installation: `python -m pip install .`, then use `logbrief build.log`.

## How it works

1. Strip ANSI color codes and mask common credential patterns.
2. Select error-keyword lines, newest first, within the requested line budget.
3. Preserve complete ordinary Python traceback blocks when the remaining line budget fits; otherwise retain prioritized error lines. Add surrounding lines, then fill remaining space with recent output.
4. Restore chronological order, fold adjacent identical lines, and show omitted ranges.

Example input: three `waiting` lines, `error: compilation failed`, `source.c:12`.

```text
LogBrief: 5/5 lines; 1 error matches; 0 omitted
[1-3 x3] waiting
[4] error: compilation failed
[5] source.c:12
```

`--max-lines` limits selected source lines before folding, not tokens, bytes or total rendered lines. JSON exposes `input_lines`, `selected_lines`, `omitted_lines`, `error_lines`, and entries with original start/end positions. Redaction happens before selection. Errors are keyword matches, not semantic diagnosis; omitted content may be relevant. Input is read into memory, so split very large logs first. UTF-8 files with invalid bytes use replacement characters.

Credential masking is best effort, not a security guarantee. Review summaries before sharing; arbitrary personal data and unknown secret formats are not detected. This tool never uploads logs or executes their contents.

## Development

```sh
python -m unittest -v
```

The initial tests cover failure retention amid noise, budgets, line numbers, repetition, credential masking, empty input and the CLI. CI is configured for Windows/Linux and Python 3.10/3.13; local results are recorded separately.

## Roadmap

- Extend traceback support to exception groups and nonstandard log prefixes.
- Add configurable keyword patterns and redaction rules.
- Stream large files with bounded memory.

Inspired by interest in coding-agent context efficiency on [GitHub Trending](https://github.com/trending), including [context-mode](https://github.com/mksglu/context-mode). Independently implemented; no upstream code copied.

MIT licensed. Contributions welcome: include a sanitized reproducer and expected output.
