"""Tests for the processing module."""

import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from lintquarto.gather import gather_qmd_files
from lintquarto.main import validate_no_commas
from lintquarto.runner import lint_qmd

CORE_LINTER = "flake8"


# =============================================================================
# 1. lint_qmd()
# =============================================================================


def test_lint_qmd_with_real_file(tmp_path):
    """Integration Test: lint_qmd runs on a real .qmd file."""
    # Create a temporary quarto file
    qmd_file = tmp_path / "test.qmd"
    qmd_file.write_text("# Test Quarto file\n``````")

    # Call lint_qmd and attempt to lint it - should return a valid exit code
    result = lint_qmd(str(qmd_file), CORE_LINTER)
    assert result in (0, 1)


def test_lint_qmd_invalid_file(tmp_path):
    """Integration Test: lint_qmd returns error for invalid file."""
    # Run on a file that doesn't exist
    result = lint_qmd(str(tmp_path / "notfound.qmd"), CORE_LINTER)
    assert result == 1

    # Create a text file and attempt to run lint_qmd()
    txt_file = tmp_path / "file.txt"
    txt_file.write_text("print('hello')")
    result = lint_qmd(str(txt_file), CORE_LINTER)
    assert result == 1


def test_lint_qmd_keep_temp(tmp_path):
    """Integration Test: lint_qmd keeps the temporary .py file."""
    # Create a temporary quarto file
    qmd_file = tmp_path / "test.qmd"
    qmd_file.write_text("# Test Quarto file\n``````")

    # Call lint_qmd and attempt to lint it
    _ = lint_qmd(str(qmd_file), CORE_LINTER, keep_temp_files=True)

    # Assert that the .py file still exists after lint_qmd returns
    py_file = tmp_path / "test.py"
    assert py_file.exists(), (
        "Temporary .py file should be kept when keep_temp_files=True"
    )


def test_lint_qmd_pylint_filepath(capsys):
    """Checks filepath in pylint output is not repeating folder names."""
    # Get path to the example QMD file that already produces pylint warnings.
    # This ensures we will have some output to check.
    test_dir = Path(__file__).parent
    qmd_path = test_dir / "examples" / "general_example.qmd"

    # Run lint_qmd with pylint on the example file and capture output.
    _ = lint_qmd(qmd_path, "pylint", keep_temp_files=False, verbose=True)
    output = capsys.readouterr().out

    # Use regex to extract every filename prefix used in diagnostic lines.
    # Each pylint diagnostic typically looks like:
    #   filename.qmd:LINE:COL: CODE: message
    pattern = re.compile(r"^(.*\.qmd):\d+:\d+", re.MULTILINE)
    paths = pattern.findall(output)

    # There should be at least one path in the pylint output.
    assert paths, f"No qmd filepaths found in pylint output:\n{output}"

    # Define the expected relative path format used for test examples
    expected_rel = str(Path("tests/examples/general_example.qmd"))

    # Check there is not duplicated folder (tests/examples/.../tests/examples/)
    # If it starts with "tests/examples/", path must be exact match
    for p in paths:
        assert not p.startswith("tests/examples/") or p == expected_rel, (
            f"Invalid filepath in pylint output: {p}\nFull output:\n{output}"
        )


def test_filename_warning():
    """Check unique filename doesn't cause linting error."""
    # Fetch the example file (which has existing .py file of same name)
    test_dir = Path(__file__).parent
    qmd_path = test_dir / "examples" / "existing_file.qmd"

    # Run lintquarto on the file
    result = subprocess.run(
        [sys.executable, "-m", "lintquarto", "-l", "pylint", "-p", qmd_path],
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr

    # Check for invalid name warning
    assert "C0103" not in output


# =============================================================================
# 2. gather_qmd()
# =============================================================================


def test_gather_qmd_files_with_real_files(tmp_path):
    """Integration Test: gather_qmd_files finds .qmd files in a directory."""
    # Create two .qmd files and one .txt file in the temp directory
    (tmp_path / "a.qmd").write_text("A")
    (tmp_path / "b.qmd").write_text("B")
    (tmp_path / "c.txt").write_text("C")

    # Call gather_qmd_files and assert that only .qmd files are returned
    files = gather_qmd_files([str(tmp_path)], exclude=[])
    assert set(files) == {str(tmp_path / "a.qmd"), str(tmp_path / "b.qmd")}


def test_gather_skips_directories(tmp_path):
    """Directories with a .qmd suffix are skipped."""
    quarto_dir = tmp_path / "a.qmd"
    quarto_dir.mkdir(parents=True)

    nested_path = quarto_dir / "a.qmd"
    unnested_path = tmp_path / "b.qmd"
    nested_path.write_text("A")
    unnested_path.write_text("B")

    files = gather_qmd_files([str(tmp_path)], exclude=[])
    assert set(files) == {str(unnested_path), str(nested_path)}


def test_gather_qmd_files_exclude(tmp_path):
    """Integration Test: gather_qmd_files respects the exclude parameter."""
    # Create some temporary files
    (tmp_path / "a.qmd").write_text("A")
    (tmp_path / "b.qmd").write_text("B")
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "c.qmd").write_text("C")

    # Exclude b.qmd and subdir
    files = gather_qmd_files(
        [str(tmp_path)],
        exclude=[str(tmp_path / "b.qmd"), str(subdir)],
    )
    assert set(files) == {str(tmp_path / "a.qmd")}


# =============================================================================
# 3. validate_no_commas()
# =============================================================================


def test_validate_no_commas():
    """Unit Test: raises ValueError when path contains a comma."""
    with pytest.raises(ValueError, match="contains a comma"):
        validate_no_commas(["file1.qmd,dir2"], "paths")


# =============================================================================
# 4. temp_py_file()
# =============================================================================


def test_temp_file_cleaned_up_on_success(tmp_path):
    """Confirm temporary file is cleaned up following successful fun."""
    qmd_file = tmp_path / "test.qmd"
    qmd_file.write_text("```{python}\nx = 1\n```\n")

    lint_qmd(qmd_file, linter="flake8")

    assert not any(tmp_path.glob("*.py"))


def test_temp_file_cleaned_up_on_exception(tmp_path):
    """For error during processing, temp file should still be removed."""
    qmd_file = tmp_path / "test.qmd"
    qmd_file.write_text("```{python}\nx = 1\n```\n")

    with patch(
        "lintquarto.runner.subprocess.run",
        side_effect=RuntimeError("boom"),
    ):
        ret = lint_qmd(qmd_file, linter="flake8")

    assert ret == 1
    assert not any(tmp_path.glob("*.py"))


def test_temp_file_kept_when_flag_set(tmp_path):
    """Temporary files kept if keep_temp_files=True."""
    qmd_file = tmp_path / "test.qmd"
    qmd_file.write_text("```{python}\nx = 1\n```\n")

    lint_qmd(qmd_file, linter="flake8", keep_temp_files=True)

    assert len(list(tmp_path.glob("*.py"))) == 1
