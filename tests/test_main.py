"""Integration and functional tests for the __main__ module."""

import subprocess
import sys

from lintquarto.__main__ import gather_qmd_files, process_qmd


# =============================================================================
# 1. process_qmd()
# =============================================================================

def test_process_qmd_with_real_file(tmp_path):
    """
    Integration Test: process_qmd runs on a real .qmd file.

    It is integration as it verifies the interaction between the file system,
    the linter logic, and the conversion process, but does not run the full CLI
    or simulate user commands.
    """

    # Create a temporary quarto file
    qmd_file = tmp_path / "test.qmd"
    qmd_file.write_text("# Test Quarto file\n``````")

    # Call process_qmd and attempt to lint it - should return a valid exit code
    result = process_qmd(str(qmd_file), "flake8")
    assert result in (0, 1)


# =============================================================================
# 2. gather_qmd()
# =============================================================================

def test_gather_qmd_files_with_real_files(tmp_path):
    """
    Integration Test: gather_qmd_files finds .qmd files in a directory.

    It is integration as it checks that the function correctly finds .qmd
    files, integrating file system access and filtering logic, but does not
    involve the full application flow.
    """

    # Create two .qmd files and one .txt file in the temp directory
    (tmp_path / "a.qmd").write_text("A")
    (tmp_path / "b.qmd").write_text("B")
    (tmp_path / "c.txt").write_text("C")

    # Call gather_qmd_files and assert that only .qmd files are returned
    files = gather_qmd_files([str(tmp_path)], exclude=[])
    assert set(files) == {str(tmp_path / "a.qmd"), str(tmp_path / "b.qmd")}


# =============================================================================
# 3. __main__()
# =============================================================================

def test_main_runs_functional(tmp_path):
    """
    Functional Test: main() runs as a CLI entry point on real .qmd file.

    It is functional as it tests the full workflow.
    """

    # Create a .qmd file for linting
    qmd_file = tmp_path / "test.qmd"
    qmd_file.write_text("# Test\n``````")

    # Run the CLI tool as a subprocess, mimicking user command-line usage and
    # assert that the process exits with a valid code
    result = subprocess.run(
        [sys.executable, "-m", "lintquarto", "flake8", str(qmd_file)],
        capture_output=True,
        text=True,
        check=False
    )
    assert result.returncode in (0, 1)


def test_main_no_qmd_files_functional(tmp_path):
    """
    Functional Test: main() exits with error if no .qmd files are found.

    It is functional as it tests the whole workflow.
    """
    # Attempt to lint a non-existent .qmd file
    result = subprocess.run(
        [sys.executable, "-m", "lintquarto", "flake8",
         str(tmp_path / "nofiles")],
        capture_output=True,
        text=True,
        check=False
    )

    # Assert that the exit code is 1 (error), and that error message is present
    assert result.returncode == 1
    assert "No .qmd files found" in result.stderr
