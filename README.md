# dlen

Check how long your functions and classes are.

A long function is the cheapest smell to detect and the most reliable one to act on.
`dlen` tells you which ones crossed the line, and where.

```console
$ dlen src/
src/importer.py:42:1: DL001 function 'process_batch' is 34 lines (max 20)
src/importer.py:88:5: DL001 function 'validate' is 14 lines (warn 12)
src/models.py:7:1: DL002 class 'LegacyRecord' is 812 lines (max 500)
```

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
| `--warn-function N` | 30 | report a function above N lines, without failing |
| `--max-function N` | 50 | fail on a function above N lines |
| `--max-class N` | 500 | fail on a class above N lines |
| `--output-format` | `full` | `full`, `github` or `json` |

A function's length includes its decorators — they are part of what you read before
you understand it.

### Where the defaults come from

They were measured, not chosen. Across 29,000 functions in the Python standard library,
numpy, Pillow, rich, pytest, httpx, mypy and coverage:

| | median | p75 | p90 | over 20 lines |
| --- | --- | --- | --- | --- |
| Python standard library | 7 | 14 | 30 | 16% |
| mypy | 7 | 17 | 37 | 21% |
| pytest | 9 | 18 | 34 | 22% |
| httpx | 9 | 19 | 34 | 23% |
| rich | 10 | 22 | 41 | 27% |
| Pillow | 10 | 23 | 51 | 27% |
| numpy | 14 | 46 | 82 | 43% |

The median function out there is 7 to 14 lines, which is reassuring and remarkably stable
across eight independent codebases. The tail is what a default has to answer to: a limit
of 20 flags a sixth of the standard library and a quarter of rich. That is not a warning,
it is a wall — and a tool that fires on a quarter of your code gets uninstalled on the
first day.

At 50 — the number `pylint` and `ruff` already use for statements — you flag around 5%.
That is a list you can work through on a Tuesday.

The class limit is a different story: 500 fires on about 1% of standard library classes,
and when it fires it is right. It stays where it was.

If you want the stricter Clean Code reading, it is one flag away:

```console
dlen src/ --warn-function 12 --max-function 20
```

Versions before 0.2.0 shipped 12 and 20 as the defaults.

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
