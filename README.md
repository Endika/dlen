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
| `--warn-function N` | 12 | report a function above N lines, without failing |
| `--max-function N` | 20 | fail on a function above N lines |
| `--max-class N` | 500 | fail on a class above N lines |
| `--output-format` | `full` | `full`, `github` or `json` |

A function's length includes its decorators — they are part of what you read before
you understand it.

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
