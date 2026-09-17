# dlen

Check how long your functions and classes are.

A long function is the cheapest smell to detect and the most reliable one to act on.
`dlen` tells you which ones crossed the line, and where.

```console
$ dlen src/
src/importer.py:42:1: DL001 function 'process_batch' is 61 lines (max 40)
src/importer.py:88:5: DL001 function 'validate' is 28 lines (warn 25)
src/models.py:7:1: DL002 class 'LegacyRecord' is 812 lines (max 500)
```

It counts the code you have to read: not the docstring, not the blank lines.

## Install

```console
uv tool install dlen     # or: pipx install dlen, pip install dlen
```

Python 3.10 or newer. No dependencies.

## Use

```console
dlen src/ tests/                 # files, directories, or both
dlen . --max-function 30         # your project, your thresholds
dlen . --output-format=json      # for other tools
```

| Flag | Default | Meaning |
| --- | --- | --- |
| `--warn-function N` | 25 | report a function above N lines, without failing |
| `--max-function N` | 40 | fail on a function above N lines |
| `--max-class N` | 500 | fail on a class above N lines |
| `--output-format` | `full` | `full`, `github` or `json` |

### What counts as a line

Decorators count — they are part of what you read before you understand the function.

**Docstrings and blank lines do not.** Counting them meant punishing you for documenting:
a well-written docstring pushed a short function over the limit. `rich.inspect` is 54
lines on screen and 7 statements of code; flagging it was simply wrong.

Comments do count. They are text you read to understand the code, not text that describes
the interface.

### Where the defaults come from

They were measured, not chosen. Over 28,390 functions in the Python standard library,
numpy, Pillow, rich, pytest, httpx, mypy and coverage, counted the way above:

| lines | functions flagged |
| --- | --- |
| over 12 | 25.0% |
| over 20 | 14.6% |
| **over 25** | **10.8%** ← `--warn-function` |
| over 30 | 8.3% |
| **over 40** | **5.3%** ← `--max-function` |
| over 50 | 3.6% |

The median function out there is **5 lines**, and that holds across all eight codebases.
`--max-function` sits where it flags about 5% — a list you can work through on a Tuesday —
and `--warn-function` around 10%, close enough to notice before it becomes a problem.

The class limit is the one number from 2017 the data supports: 500 flags 2.2% of classes,
and a class that long really is a god object. It stays.

If you want the stricter Clean Code reading, it is one flag away:

```console
dlen src/ --warn-function 12 --max-function 20
```

Versions before 0.2.0 shipped 12 and 20. 0.3.0 stopped counting docstrings and blank
lines, which made every function measure shorter, so the thresholds came down with it.

### Exit codes

| Code | When |
| --- | --- |
| `0` | nothing found, or only warnings |
| `1` | something was over a `max`, or a file could not be parsed |
| `2` | bad arguments |

Warnings never fail the build. That is the point of having two thresholds: one to
nudge, one to stop.

### Rules

| Code | Rule |
| --- | --- |
| `DL001` | function is too long |
| `DL002` | class is too long |
| `DL900` | file could not be read or parsed |

## In CI

`--output-format=github` puts each finding on the diff of the pull request instead
of burying it in a log:

```yaml
- run: uvx dlen src --output-format=github
```

## As a library

The core returns data and prints nothing, so you can build your own reporting on it:

```python
from pathlib import Path
from dlen import Limits, check_paths

findings = check_paths([Path("src")], Limits(max_function=30))
for finding in findings:
    print(finding.code, finding.path, finding.line, finding.message)
```

Every call returns a fresh list. Two runs never see each other's findings.

## How it measures

`dlen` parses your code with Python's own `ast` module, so it agrees with Python
about what a function is. It sees `async def`, decorators, nested functions and
methods, and it is not fooled by the word `def` inside a string or a comment.

> Versions before 0.1.0 matched text with regular expressions and had been broken on
> Python 3 since 2017. 0.1.0 is a rewrite: the counts are now correct rather than
> compatible, and the output carries file, line and column.

## Licence

MIT.
