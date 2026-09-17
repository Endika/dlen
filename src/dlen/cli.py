"""The command line: parses arguments, renders findings, picks the exit code.

This is the only module that prints or reads argv. The core stays a pure function
of its inputs, which is what makes it usable from another program.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .core import Finding, Level, Limits, check_paths

DEFAULTS = Limits()


def format_full(findings: Sequence[Finding]) -> str:
    """One line per finding, the shape editors and CI logs already know how to parse."""
    return "\n".join(f"{f.path}:{f.line}:{f.column}: {f.code.value} {f.message}" for f in findings)


def format_github(findings: Sequence[Finding]) -> str:
    """Workflow commands, so the findings land on the PR diff instead of in a log."""
    return "\n".join(
        f"::{f.level.value} file={f.path},line={f.line},col={f.column},"
        f"title={f.code.value}::{f.message}"
        for f in findings
    )


def _as_dict(finding: Finding) -> dict[str, str | int]:
    return {
        "path": str(finding.path),
        "line": finding.line,
        "column": finding.column,
        "code": finding.code.value,
        "level": finding.level.value,
        "message": finding.message,
    }


def format_json(findings: Sequence[Finding]) -> str:
    return json.dumps([_as_dict(f) for f in findings], indent=2)


FORMATTERS = {"full": format_full, "github": format_github, "json": format_json}


def _add_limit(parser: argparse.ArgumentParser, flag: str, default: int, verb: str) -> None:
    parser.add_argument(
        flag,
        type=int,
        default=default,
        metavar="N",
        help=f"{verb} above N lines (default: {default})",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dlen", description="Check how long your functions and classes are."
    )
    parser.add_argument("paths", nargs="+", type=Path, metavar="PATH", help="files or directories")
    _add_limit(parser, "--warn-function", DEFAULTS.warn_function, "warn")
    _add_limit(parser, "--max-function", DEFAULTS.max_function, "fail")
    _add_limit(parser, "--max-class", DEFAULTS.max_class, "fail")
    parser.add_argument(
        "--output-format", choices=sorted(FORMATTERS), default="full", metavar="FORMAT"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Returns the exit code: 1 when anything is over a max, 0 otherwise."""
    args = build_parser().parse_args(argv)
    limits = Limits(args.warn_function, args.max_function, args.max_class)

    findings = check_paths(args.paths, limits)
    if findings:
        print(FORMATTERS[args.output_format](findings))

    return 1 if any(f.level is Level.ERROR for f in findings) else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
