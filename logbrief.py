"""Deterministic, local-only build log summaries. Python 3.10+."""
import argparse
import json
import re
import sys
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
ERROR = re.compile(r"\b(error|failed|failure|exception|traceback|fatal|panic)\b", re.I)
EXCEPTION_HEADER = re.compile(r"^\s*(?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*(?:Error|Exception)\s*:")
SECRETS = [
    (re.compile(r"(?i)([\"'](?:api[_-]?key|token|password|secret)[\"']\s*:\s*)(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')"), r'\1"[REDACTED]"'),
    (re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,})\b"), "[REDACTED]"),
    (re.compile(r"(?i)(\b(?:api[_-]?key|token|password|secret)\b\s*[:=]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(\bBearer\s+)\S+"), r"\1[REDACTED]"),
    (re.compile(r"(https?://)[^/\s:@]+:[^/\s@]+@"), r"\1[REDACTED]@"),
]


def clean(text):
    text = ANSI.sub("", text)
    for pattern, replacement in SECRETS:
        text = pattern.sub(replacement, text)
    return text


def summarize(text, max_lines=80, context=2, matches=None):
    if max_lines < 1 or context < 0:
        raise ValueError("max_lines must be positive and context nonnegative")
    lines = clean(text).splitlines()
    keywords = [match.casefold() for match in (matches or []) if match.strip()]
    hits = [i for i, line in enumerate(lines) if ERROR.search(line) or EXCEPTION_HEADER.search(line)
            or any(keyword in line.casefold() for keyword in keywords)]
    # Prefer recent failures, then nearby context, then the final output.
    priority = list(reversed(hits))
    for distance in range(1, context + 1):
        for i in reversed(hits):
            priority.extend([i + distance, i - distance])
    priority.extend(range(len(lines) - 1, -1, -1))
    selected = set(list(reversed(hits))[:max_lines])
    # Keep ordinary Python traceback frames together when the remaining budget fits.
    groups = []
    start = None
    for i, line in enumerate(lines):
        if line.strip() == 'Traceback (most recent call last):':
            start = i
        elif start is not None and EXCEPTION_HEADER.search(line):
            groups.append((start, i))
            start = None
        elif start is not None and line and not line[0].isspace():
            start = None
    for start, end in reversed(groups):
        group = set(range(start, end + 1))
        if len(selected | group) <= max_lines:
            selected.update(group)
    for i in priority:
        if len(selected) >= max_lines:
            break
        if 0 <= i < len(lines):
            selected.add(i)
    entries = []
    for i in sorted(selected):
        if entries and entries[-1]["end"] == i and entries[-1]["text"] == lines[i]:
            entries[-1]["end"] = i + 1
            entries[-1]["repeat"] += 1
        else:
            entries.append(dict(start=i + 1, end=i + 1, text=lines[i], repeat=1))
    return dict(input_lines=len(lines), selected_lines=len(selected),
                omitted_lines=len(lines) - len(selected), error_lines=len(hits), entries=entries)


def render(result):
    output = [f"LogBrief: {result['selected_lines']}/{result['input_lines']} lines; "
              f"{result['error_lines']} error matches; {result['omitted_lines']} omitted"]
    previous = 0
    for item in result["entries"]:
        if item["start"] > previous + 1:
            output.append(f"... {item['start'] - previous - 1} lines omitted ...")
        label = str(item["start"])
        if item["repeat"] > 1:
            label += f"-{item['end']} x{item['repeat']}"
        output.append(f"[{label}] {item['text']}")
        previous = item["end"]
    if previous < result["input_lines"]:
        output.append(f"... {result['input_lines'] - previous} lines omitted ...")
    return "\n".join(output) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", default="-", help="UTF-8 log file, or - for stdin")
    parser.add_argument("--max-lines", type=int, default=80)
    parser.add_argument("--context", type=int, default=2)
    parser.add_argument("--json", action="store_true", help="machine-readable summary")
    parser.add_argument("--match", action="append", default=[], metavar="TEXT",
                        help="additional case-insensitive literal priority text; repeatable")
    args = parser.parse_args(argv)
    if args.max_lines < 1 or args.context < 0:
        parser.error("--max-lines must be positive; --context must be nonnegative")
    try:
        text = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8", errors="replace")
        result = summarize(text, args.max_lines, args.context, matches=args.match)
        print(json.dumps(result, ensure_ascii=True, indent=2) if args.json else render(result), end="\n" if args.json else "")
    except (OSError, UnicodeError) as exc:
        parser.exit(2, f"logbrief: {exc}\n")


if __name__ == "__main__":
    main()
