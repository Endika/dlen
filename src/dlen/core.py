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
    """The three thresholds, defaulting to the ones dlen has used since 2017."""

    warn_function: int = 12
    max_function: int = 20
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


def _span(node: Definition) -> int:
    """Lines the node covers, decorators included — they are part of what you read."""
    start = min([node.lineno, *(d.lineno for d in node.decorator_list)])
    end = node.end_lineno if node.end_lineno is not None else node.lineno
    return end - start + 1


def _finding(node: Definition, path: Path, code: Code, level: Level, text: str) -> Finding:
    return Finding(path, node.lineno, node.col_offset + 1, code, level, text)


def _describe(kind: str, name: str, length: int, limit: int, level: Level) -> str:
    threshold = "max" if level is Level.ERROR else "warn"
    return f"{kind} {name!r} is {length} lines ({threshold} {limit})"


def _check_function(node: Function, path: Path, limits: Limits) -> Finding | None:
    length = _span(node)
    if length > limits.max_function:
        level, limit = Level.ERROR, limits.max_function
    elif length > limits.warn_function:
        level, limit = Level.WARNING, limits.warn_function
    else:
        return None
    text = _describe("function", node.name, length, limit, level)
    return _finding(node, path, Code.FUNCTION_TOO_LONG, level, text)


def _check_class(node: ast.ClassDef, path: Path, limits: Limits) -> Finding | None:
    length = _span(node)
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

    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            found = _check_class(node, path, limits)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            found = _check_function(node, path, limits)
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
