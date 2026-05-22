"""Tests for correct handling of IPython cell magic lines."""

from __future__ import annotations

import pytest

from lintquarto.converter import QmdToPyConverter

LINTERS_NOQA = ["flake8", "pycodestyle", "ruff"]
LINTERS_ALL = [
    "flake8",
    "mypy",
    "pycodestyle",
    "pydoclint",
    "pyflakes",
    "pylint",
    "pyrefly",
    "pyright",
    "pytype",
    "radon-cc",
    "radon-mi",
    "radon-raw",
    "radon-hal",
    "ruff",
    "vulture",
]

CELL_MAGICS = [
    pytest.param("%%prun", id="prun"),
    pytest.param("%%prun -T prof.txt", id="prun_with_args"),
    pytest.param("%%timeit", id="timeit"),
    pytest.param("%%timeit -n 100", id="timeit_with_args"),
    pytest.param("%%time", id="time"),
    pytest.param("%%capture", id="capture"),
    pytest.param("%%capture out", id="capture_with_var"),
    pytest.param("%%debug", id="debug"),
]


@pytest.mark.parametrize("magic_line", CELL_MAGICS)
@pytest.mark.parametrize("linter", LINTERS_ALL)
def test_cell_magic_line_not_in_output(magic_line: str, linter: str) -> None:
    """Check %magic line is not in the converted output."""
    lines = [
        "```{python}",
        magic_line,
        "x = 1",
        "```",
    ]
    result = QmdToPyConverter(linter=linter).convert(lines)
    magic_keyword = magic_line.split(maxsplit=1)[0]  # e.g. "%%prun"
    assert not any(magic_keyword in line for line in result), (
        f"Magic '{magic_keyword}' should not appear in converted output "
        f"(linter={linter}).\nOutput: {result}"
    )


@pytest.mark.parametrize("magic_line", CELL_MAGICS)
def test_cell_magic_line_becomes_placeholder(magic_line: str) -> None:
    """Check %%magic line id converted to placeholder."""
    lines = [
        "```{python}",
        magic_line,
        "x = 1",
        "```",
    ]
    result = QmdToPyConverter(linter="ruff").convert(lines)
    # Output line at same index as magic_line input should be a placeholder
    # (index 1, since index 0 is the chunk opener → "# %% [python]")
    assert result[1] == "# -", (
        f"Expected placeholder '# -' at position 1 for magic "
        f"'{magic_line}'.\nFull output: {result}"
    )


@pytest.mark.parametrize("magic_line", CELL_MAGICS)
def test_line_count_preserved_with_cell_magic(magic_line: str) -> None:
    """Line count must be preserved when a cell magic is present."""
    lines = [
        "```{python}",
        magic_line,
        "x = 1",
        "```",
    ]
    result = QmdToPyConverter(linter="ruff").convert(lines)
    assert len(result) == len(lines), (
        f"Line count mismatch for magic '{magic_line}'.\n"
        f"Input  ({len(lines)}): {lines}\n"
        f"Output ({len(result)}): {result}"
    )


@pytest.mark.parametrize("magic_line", CELL_MAGICS)
def test_python_magic_body_passes_through(magic_line: str) -> None:
    """Test lines after Python cell magic are still present."""
    lines = [
        "```{python}",
        magic_line,
        "result = sum(range(100))",
        "```",
    ]
    result = QmdToPyConverter(linter="ruff").convert(lines)
    assert any("result = sum(range(100))" in line for line in result), (
        "Body code should pass through for python-style magic "
        f"'{magic_line}'.\n Output: {result}"
    )


# ---------------------------------------------------------------------------
# Minimal reproducer from the bug report
# ---------------------------------------------------------------------------


def test_prun_minimal_reproducer() -> None:
    """
    Exact reproducer from the issue report.

        ```{python}
        def slow_function():
            ...
        ```

        ```{python}
        %%prun -T prof-slow-fn.txt
        slow_function()
        ```

    After a fix:
    - %%prun line → placeholder (not raw Python with noqa)
    - slow_function() → passes through (it's valid Python)
    - line count preserved
    """
    lines = [
        "```{python}",
        "def slow_function():",
        "    total = 0",
        "    for i in range(100000):",
        "        total += i * i",
        "    return total",
        "```",
        "",
        "```{python}",
        "%%prun -T prof-slow-fn.txt",
        "slow_function()",
        "```",
    ]
    result = QmdToPyConverter(linter="ruff").convert(lines)

    # %%prun must not appear as raw Python in output
    assert not any("%%prun" in line for line in result), (
        f"%%prun should not appear in output.\nprun lines: "
        f"{[line for line in result if '%%prun' in line]}"
    )

    # slow_function() call should still be present
    assert any("slow_function()" in line for line in result), (
        "slow_function() body should pass through after %%prun."
    )

    # Line count preserved
    assert len(result) == len(lines), (
        f"Line count mismatch: input={len(lines)}, output={len(result)}"
    )
