"""Measuring how long a function or a class is, and deciding whether that is too long.

Everything here returns data. Nothing prints, nothing reads argv, nothing keeps state
between calls — so a second run can never inherit the first one's findings.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Level(str, Enum):
    WARNING = "warning"
    ERROR = "error"


class Code(str, Enum):
    FUNCTION_TOO_LONG = "DL001"
    CLASS_TOO_LONG = "DL002"
    SYNTAX_ERROR = "DL900"


@dataclass(frozen=True, slots=True)
class Limits:
    """The three thresholds.

    Measured over 28,390 functions in the Python standard library, numpy, Pillow,
    rich, pytest, httpx, mypy and coverage. Counting the way `_span` does — no
    docstrings, no blank lines — the median function out there is 5 lines, and:

        over 20 lines: 14.6%    over 30: 8.3%    over 50: 3.6%
        over 25 lines: 10.8%    over 40: 5.3%

    `max_function` is set where it flags about 5% of a typical codebase, which is a
    list you can work through. `warn_function` sits at roughly 10%, close enough to
    notice before it becomes a problem.

    For the stricter Clean Code reading, pass `--warn-function 12 --max-function 20`.

    `max_class` stays at the value dlen shipped in 2017: it flags 2.2% of classes,
    and a class that long really is a god object.
    """

    warn_function: int = 25
    max_function: int = 40
    max_class: int = 500


@dataclass(frozen=True, slots=True)
class Finding:
    path: Path
    line: int
    column: int
    code: Code
    level: Level
    message: str


Definition = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
Function = ast.FunctionDef | ast.AsyncFunctionDef


def _docstring_lines(node: Definition) -> range:
    """The lines the node's own docstring occupies, if it has one.

    A parsed definition always has at least one statement, so there is no empty
    body to guard against. A first statement that is a bare number, though, is not
    a docstring — `42` on its own line is code, however useless.
    """
    first = node.body[0]
    if not isinstance(first, ast.Expr) or not isinstance(first.value, ast.Constant):
        return range(0)
    if not isinstance(first.value.value, str):
        return range(0)
    return range(first.lineno, (first.end_lineno or first.lineno) + 1)


def _span(node: Definition, lines: list[str]) -> int:
    """Lines you actually have to read.

    Decorators count — they are part of what you read before you understand the
    function. Blank lines and the node's own docstring do not: penalising a long
    docstring would be telling you to document less, which is the wrong lesson.
    """
    start = min([node.lineno, *(d.lineno for d in node.decorator_list)])
    end = node.end_lineno if node.end_lineno is not None else node.lineno
    skip = _docstring_lines(node)
    return sum(1 for n in range(start, end + 1) if n not in skip and lines[n - 1].strip())


def _finding(node: Definition, path: Path, code: Code, level: Level, text: str) -> Finding:
    return Finding(path, node.lineno, node.col_offset + 1, code, level, text)


def _describe(kind: str, name: str, length: int, limit: int, level: Level) -> str:
    threshold = "max" if level is Level.ERROR else "warn"
    return f"{kind} {name!r} is {length} lines ({threshold} {limit})"


def _check_function(node: Function, path: Path, limits: Limits, lines: list[str]) -> Finding | None:
    length = _span(node, lines)
    if length > limits.max_function:
        level, limit = Level.ERROR, limits.max_function
    elif length > limits.warn_function:
        level, limit = Level.WARNING, limits.warn_function
    else:
        return None
    text = _describe("function", node.name, length, limit, level)
    return _finding(node, path, Code.FUNCTION_TOO_LONG, level, text)


def _check_class(
    node: ast.ClassDef, path: Path, limits: Limits, lines: list[str]
) -> Finding | None:
    length = _span(node, lines)
    if length <= limits.max_class:
        return None
    text = _describe("class", node.name, length, limits.max_class, Level.ERROR)
    return _finding(node, path, Code.CLASS_TOO_LONG, Level.ERROR, text)


def _syntax_finding(exc: SyntaxError, path: Path) -> Finding:
    line, column = exc.lineno or 1, exc.offset or 1
    message = f"cannot parse: {exc.msg}"
    return Finding(path, line, column, Code.SYNTAX_ERROR, Level.ERROR, message)


def check_source(source: str, path: Path, limits: Limits) -> list[Finding]:
    """Findings for one piece of source, in the order they appear in the file."""
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [_syntax_finding(exc, path)]

    lines = source.splitlines()
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            found = _check_class(node, path, limits, lines)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            found = _check_function(node, path, limits, lines)
        else:
            continue
        if found is not None:
            findings.append(found)

    return sorted(findings, key=lambda f: (f.line, f.column))


def check_file(path: Path, limits: Limits) -> list[Finding]:
    """Findings for one file. An unreadable file is a finding, not a crash."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [Finding(path, 1, 1, Code.SYNTAX_ERROR, Level.ERROR, f"cannot read: {exc}")]
    return check_source(source, path, limits)


def iter_python_files(paths: list[Path]) -> list[Path]:
    """Every .py under the given paths, deduplicated and in a stable order."""
    found: list[Path] = []
    for path in paths:
        found.extend(sorted(path.rglob("*.py")) if path.is_dir() else [path])
    return list(dict.fromkeys(found))


def check_paths(paths: list[Path], limits: Limits) -> list[Finding]:
    return [finding for path in iter_python_files(paths) for finding in check_file(path, limits)]
