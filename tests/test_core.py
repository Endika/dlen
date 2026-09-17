"""The engine against the shapes real Python takes."""

from __future__ import annotations

from pathlib import Path

import pytest

from dlen.core import Code, Level, Limits, check_file, check_paths, check_source

HERE = Path("sample.py")

# Los tests de forma fijan sus umbrales: lo que prueban es la detección, no los defaults.
STRICT = Limits(warn_function=12, max_function=20, max_class=500)


def body(lines: int, indent: str = "    ") -> str:
    return "".join(f"{indent}x = {i}\n" for i in range(lines))


def test_a_short_function_is_not_reported() -> None:
    findings = check_source(f"def short():\n{body(3)}", HERE, STRICT)

    assert findings == []


def test_a_long_function_is_an_error_with_its_position() -> None:
    (finding,) = check_source(f"def long_one():\n{body(30)}", HERE, STRICT)

    assert finding.code is Code.FUNCTION_TOO_LONG
    assert finding.level is Level.ERROR
    assert (finding.line, finding.column) == (1, 1)
    assert finding.message == "function 'long_one' is 31 lines (max 20)"


def test_a_middling_function_is_only_a_warning() -> None:
    (finding,) = check_source(f"def middling():\n{body(15)}", HERE, STRICT)

    assert finding.level is Level.WARNING
    assert "warn 12" in finding.message


def test_thresholds_are_honoured() -> None:
    source = f"def middling():\n{body(15)}"

    assert check_source(source, HERE, Limits(warn_function=50, max_function=60)) == []


class TestShapesTheRegexEngineGotWrong:
    """Each of these was a false positive or a miss before the ast rewrite."""

    def test_a_decorator_counts_as_part_of_the_function(self) -> None:
        source = "@decorator\n@another\ndef decorated():\n" + body(19)

        (finding,) = check_source(source, HERE, STRICT)

        assert finding.message == "function 'decorated' is 22 lines (max 20)"

    def test_a_signature_split_over_lines_is_one_function(self) -> None:
        source = "def wide(\n    a,\n    b,\n    c,\n):\n" + body(20)

        findings = check_source(source, HERE, STRICT)

        assert [f.message for f in findings] == ["function 'wide' is 25 lines (max 20)"]

    def test_async_functions_are_measured_too(self) -> None:
        (finding,) = check_source(f"async def fetch():\n{body(30)}", HERE, STRICT)

        assert finding.message == "function 'fetch' is 31 lines (max 20)"

    def test_a_nested_function_is_measured_on_its_own(self) -> None:
        source = (
            "def outer():\n    def inner():\n" + body(30, indent="        ") + "    return inner\n"
        )

        names = {f.message.split("'")[1] for f in check_source(source, HERE, STRICT)}

        assert names == {"outer", "inner"}

    def test_the_word_def_inside_a_string_is_not_a_function(self) -> None:
        source = 'TEXT = """\ndef not_really():\n' + body(30) + '"""\n'

        assert check_source(source, HERE, STRICT) == []

    def test_a_comment_mentioning_def_is_not_a_function(self) -> None:
        source = "# def commented_out():\n" + "x = 1\n" * 30

        assert check_source(source, HERE, STRICT) == []

    def test_methods_are_measured_and_report_their_own_column(self) -> None:
        source = "class Thing:\n    def method(self):\n" + body(30, indent="        ")

        (finding,) = [f for f in check_source(source, HERE, STRICT) if "method" in f.message]

        assert finding.column == 5


def test_a_long_class_is_reported() -> None:
    source = "class Big:\n" + body(600)

    (finding,) = [f for f in check_source(source, HERE, STRICT) if f.code is Code.CLASS_TOO_LONG]

    assert finding.message == "class 'Big' is 601 lines (max 500)"
    assert finding.level is Level.ERROR


def test_unparseable_source_is_a_finding_not_a_crash() -> None:
    (finding,) = check_source("def broken(:\n", HERE, STRICT)

    assert finding.code is Code.SYNTAX_ERROR
    assert finding.level is Level.ERROR
    assert "cannot parse" in finding.message


def test_findings_come_back_in_file_order() -> None:
    source = f"def first():\n{body(30)}\n\ndef second():\n{body(30)}"

    lines = [f.line for f in check_source(source, HERE, STRICT)]

    assert lines == sorted(lines)


def test_two_runs_do_not_contaminate_each_other() -> None:
    """The old engine kept findings on the class, so a second run inherited the first."""
    first = check_source(f"def long_one():\n{body(30)}", HERE, STRICT)
    second = check_source("def short():\n    pass\n", HERE, STRICT)

    assert len(first) == 1
    assert second == []


class TestFiles:
    def test_a_file_is_read_and_measured(self, tmp_path: Path) -> None:
        path = tmp_path / "mod.py"
        path.write_text(f"def long_one():\n{body(30)}", encoding="utf-8")

        (finding,) = check_file(path, STRICT)

        assert finding.path == path

    def test_an_unreadable_file_is_a_finding(self, tmp_path: Path) -> None:
        (finding,) = check_file(tmp_path / "missing.py", STRICT)

        assert finding.code is Code.SYNTAX_ERROR
        assert "cannot read" in finding.message

    def test_a_directory_is_walked_for_python_files_only(self, tmp_path: Path) -> None:
        (tmp_path / "pkg").mkdir()
        (tmp_path / "pkg" / "a.py").write_text(f"def a():\n{body(30)}", encoding="utf-8")
        (tmp_path / "pkg" / "notes.txt").write_text("def ignored():\n", encoding="utf-8")

        findings = check_paths([tmp_path], STRICT)

        assert [f.path.name for f in findings] == ["a.py"]

    def test_the_same_file_named_twice_is_only_checked_once(self, tmp_path: Path) -> None:
        path = tmp_path / "dup.py"
        path.write_text(f"def a():\n{body(30)}", encoding="utf-8")

        assert len(check_paths([path, path], STRICT)) == 1


@pytest.mark.parametrize("limit", [0, 1])
def test_a_tiny_limit_reports_everything(limit: int) -> None:
    findings = check_source("def one_liner():\n    pass\n", HERE, Limits(max_function=limit))

    assert len(findings) == 1


class TestTheDefaults:
    """The defaults are a claim about real code, so they get their own test."""

    def test_they_are_the_measured_ones_not_the_2017_ones(self) -> None:
        assert (Limits().warn_function, Limits().max_function) == (30, 50)
        assert Limits().max_class == 500

    def test_a_forty_line_function_only_warns(self) -> None:
        (finding,) = check_source(f"def forty():\n{body(40)}", HERE, Limits())

        assert finding.level is Level.WARNING

    def test_a_sixty_line_function_is_an_error(self) -> None:
        (finding,) = check_source(f"def sixty():\n{body(60)}", HERE, Limits())

        assert finding.level is Level.ERROR

    def test_the_median_function_out_there_is_nowhere_near_the_limit(self) -> None:
        """Median function length across the stdlib and seven big libraries is 7-14."""
        assert check_source(f"def median_sized():\n{body(14)}", HERE, Limits()) == []
