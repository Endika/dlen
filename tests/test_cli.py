"""The command line: what it prints, and what it returns to the shell."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dlen.cli import main


@pytest.fixture
def long_function(tmp_path: Path) -> Path:
    """Over the default max of 50, so it is an error without passing any flag."""
    path = tmp_path / "long.py"
    path.write_text("def long_one():\n" + "    x = 1\n" * 60, encoding="utf-8")
    return path


@pytest.fixture
def middling_function(tmp_path: Path) -> Path:
    """Between the default warn of 30 and max of 50, so it only warns."""
    path = tmp_path / "middling.py"
    path.write_text("def middling():\n" + "    x = 1\n" * 40, encoding="utf-8")
    return path


def test_a_clean_file_says_nothing_and_succeeds(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "clean.py"
    path.write_text("def short():\n    pass\n", encoding="utf-8")

    assert main([str(path)]) == 0
    assert capsys.readouterr().out == ""


def test_an_error_exits_one_so_a_ci_job_fails(
    long_function: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main([str(long_function)])

    out = capsys.readouterr().out
    assert code == 1
    assert f"{long_function}:1:1: DL001 function 'long_one' is 61 lines (max 50)" in out


def test_a_warning_is_reported_but_still_exits_zero(
    middling_function: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main([str(middling_function)])

    assert code == 0
    assert "DL001" in capsys.readouterr().out


def test_thresholds_can_be_raised_from_the_command_line(
    long_function: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main([str(long_function), "--warn-function", "80", "--max-function", "90"])

    assert code == 0
    assert capsys.readouterr().out == ""


def test_the_class_threshold_can_be_lowered(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "klass.py"
    path.write_text("class Small:\n" + "    x = 1\n" * 5, encoding="utf-8")

    code = main([str(path), "--max-class", "3"])

    assert code == 1
    assert "DL002" in capsys.readouterr().out


class TestOutputFormats:
    def test_github_format_annotates_the_diff(
        self, long_function: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        main([str(long_function), "--output-format", "github"])

        out = capsys.readouterr().out
        assert out.startswith("::error file=")
        assert "title=DL001::" in out

    def test_github_format_marks_a_warning_as_a_warning(
        self, middling_function: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        main([str(middling_function), "--output-format", "github"])

        assert capsys.readouterr().out.startswith("::warning file=")

    def test_json_format_is_machine_readable(
        self, long_function: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        main([str(long_function), "--output-format", "json"])

        payload = json.loads(capsys.readouterr().out)
        assert payload == [
            {
                "path": str(long_function),
                "line": 1,
                "column": 1,
                "code": "DL001",
                "level": "error",
                "message": "function 'long_one' is 61 lines (max 50)",
            }
        ]


def test_a_directory_is_accepted(long_function: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main([str(long_function.parent)])

    assert code == 1
    assert "long.py" in capsys.readouterr().out


def test_a_missing_path_is_an_error_not_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main([str(tmp_path / "nope.py")])

    assert code == 1
    assert "DL900" in capsys.readouterr().out


def test_no_paths_is_rejected_by_the_parser() -> None:
    with pytest.raises(SystemExit) as exit_info:
        main([])

    assert exit_info.value.code == 2
