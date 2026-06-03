"""Tests for the cli module."""

import subprocess
import sys
from pathlib import Path

import pytest

from lintquarto.cli import main

CORE_LINTER = "flake8"


def test_main_runs_functional(tmp_path):
    """Functional Test: main() runs as a CLI entry point on real .qmd file."""
    # Create a minimal .qmd file for linting
    qmd_file = tmp_path / "test.qmd"
    qmd_file.write_text("# Test\n``````")

    # Run the CLI tool as a subprocess, mimicking user command-line usage and
    # assert that the process exits with a valid code
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lintquarto",
            "-l",
            CORE_LINTER,
            "-p",
            str(qmd_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode in (0, 1)


def test_main_no_qmd_files_functional(tmp_path):
    """Functional Test: main() exits with error if no .qmd files are found."""
    # Attempt to lint a non-existent .qmd file
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lintquarto",
            "-l",
            CORE_LINTER,
            "-p",
            str(tmp_path / "nofiles"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    # Assert that the exit code is 1 (error), and that error message is present
    assert result.returncode == 1
    assert "No .qmd files found" in result.stderr


def test_decorator():
    """Functional Test: blank line warning disabled despite decorator."""
    # Locate the Quarto example file containing a function decorated with a
    # runtime-checkable decorator
    test_dir = Path(__file__).parent
    qmd_path = test_dir / "examples" / "decorator_example.qmd"

    # Run lintquarto with flake8 on the example file.
    # Normally, flake8 would raise E302 ("expected 2 blank lines before
    # function definition"), but lintquarto should suppress this warning
    result = subprocess.run(
        [sys.executable, "-m", "lintquarto", "-l", "flake8", "-p", qmd_path],
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr

    # Verify that the E302 warning does not appear in the lint output
    assert "E302" not in output


def test_eval_false():
    """Functional Test: eval=false in document YAML."""
    # Locate the Quarto example file
    test_dir = Path(__file__).parent
    qmd_path = test_dir / "examples" / "eval_example.qmd"

    # Run lintquarto with flake8 on the example file.
    result = subprocess.run(
        [sys.executable, "-m", "lintquarto", "-l", "flake8", "-p", qmd_path],
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr

    # Verify that the warnings from the second chunk (eval=True) appear
    assert "E305" in output
    assert "F401" in output
    assert "E402" in output

    # Verify that the warnings from the first chunk do not
    assert "501" not in output


def test_paths_with_commas(monkeypatch):
    """Functional Test: raises ValueError when --paths contains commas."""
    test_args = ["prog", "-l", "pylint", "-p", "file1.qmd,dir2"]
    monkeypatch.setattr(sys, "argv", test_args)
    with pytest.raises(ValueError, match="contains a comma"):
        main()


def test_exclude_with_commas(monkeypatch):
    """Functional Test: raises ValueError when --exclude contains commas."""
    test_args = [
        "prog",
        "-l",
        "pylint",
        "-p",
        "file1.qmd",
        "-e",
        "dir2,file2.qmd",
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    with pytest.raises(ValueError, match="contains a comma"):
        main()
