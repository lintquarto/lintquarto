"""
Integration and functional tests for the __main__ module.

Integration tests involves interactions between a few things (e.g. file system,
linter logic and conversion process), whilst functional tests involve running
the full workflow (e.g. simulating user commands).
"""

from pathlib import Path
import re
import subprocess
import sys

from lintquarto.__main__ import gather_qmd_files, process_qmd


CORE_LINTER = "flake8"


# =============================================================================
# 1. process_qmd()
# =============================================================================

def test_process_qmd_with_real_file(tmp_path):
    """Integration Test: process_qmd runs on a real .qmd file."""

    # Create a temporary quarto file
    qmd_file = tmp_path / "test.qmd"
    qmd_file.write_text("# Test Quarto file\n``````")

    # Call process_qmd and attempt to lint it - should return a valid exit code
    result = process_qmd(str(qmd_file), CORE_LINTER)
    assert result in (0, 1)


def test_process_qmd_invalid_file(tmp_path):
    """Integration Test: process_qmd returns error for invalid file"""

    # Run on a file that doesn't exist
    result = process_qmd(str(tmp_path / "notfound.qmd"), CORE_LINTER)
    assert result == 1

    # Create a text file and attempt to run process_qmd()
    txt_file = tmp_path / "file.txt"
    txt_file.write_text("print('hello')")
    result = process_qmd(str(txt_file), CORE_LINTER)
    assert result == 1


def test_process_qmd_keep_temp(tmp_path):
    """Integration Test: process_qmd keeps the temporary .py file."""

    # Create a temporary quarto file
    qmd_file = tmp_path / "test.qmd"
    qmd_file.write_text("# Test Quarto file\n``````")

    # Call process_qmd and attempt to lint it
    _ = process_qmd(str(qmd_file), CORE_LINTER, keep_temp_files=True)

    # Assert that the .py file still exists after process_qmd returns
    py_file = tmp_path / "test.py"
    assert py_file.exists(), (
        "Temporary .py file should be kept when keep_temp_files=True"
    )


def test_process_qmd_pylint_filepath(capsys):
    """Checks filepath in pylint output is not repeating folder names."""

    # Get path to the example QMD file that already produces pylint warnings.
    # This ensures we will have some output to check.
    test_dir = Path(__file__).parent
    qmd_path = test_dir / "examples" / "general_example.qmd"

    # Run process_qmd with pylint on the example file and capture output.
    _ = process_qmd(qmd_path, "pylint", keep_temp_files=False, verbose=True)
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
        [str(tmp_path)], exclude=[str(tmp_path / "b.qmd"), str(subdir)]
    )
    assert set(files) == {str(tmp_path / "a.qmd")}


# =============================================================================
# 3. __main__()
# =============================================================================

def test_main_runs_functional(tmp_path):
    """Functional Test: main() runs as a CLI entry point on real .qmd file."""

    # Create a minimal .qmd file for linting
    qmd_file = tmp_path / "test.qmd"
    qmd_file.write_text("# Test\n``````")

    # Run the CLI tool as a subprocess, mimicking user command-line usage and
    # assert that the process exits with a valid code
    result = subprocess.run(
        [sys.executable, "-m", "lintquarto",
         "-l", CORE_LINTER, "-p", str(qmd_file)],
        capture_output=True,
        text=True,
        check=False
    )
    assert result.returncode in (0, 1)


def test_main_no_qmd_files_functional(tmp_path):
    """Functional Test: main() exits with error if no .qmd files are found."""
    # Attempt to lint a non-existent .qmd file
    result = subprocess.run(
        [sys.executable, "-m", "lintquarto",
         "-l", CORE_LINTER, "-p", str(tmp_path / "nofiles")],
        capture_output=True,
        text=True,
        check=False
    )

    # Assert that the exit code is 1 (error), and that error message is present
    assert result.returncode == 1
    assert "No .qmd files found" in result.stderr
