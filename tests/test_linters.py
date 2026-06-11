"""Unit tests for the linters module."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from utils import skip_if_linter_unexpected

from lintquarto.registry import Linters

ALL_LINTERS = [
    "basedpyright",
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


# =============================================================================
# 1. Supported linters
# =============================================================================


def test_supported_error():
    """Test check_supported() raises ValueError for unsupported linters."""
    linters = Linters()
    with pytest.raises(
        ValueError,
        match="Unsupported linter 'unsupported_linter'",
    ):
        linters.check_supported("unsupported_linter")


@pytest.mark.parametrize("linter_name", ALL_LINTERS)
def test_supported_success(linter_name):
    """Test check_supported() returns no errors for supported linters."""
    linters = Linters()
    linters.check_supported(linter_name)


@pytest.mark.parametrize("linter_name", ["", None])
def test_supported_edge_cases(linter_name):
    """Test check_supported() raises error for empty or None linter names."""
    linters = Linters()
    with pytest.raises(ValueError, match="Unsupported linter"):
        linters.check_supported(linter_name)


@pytest.mark.parametrize("linter_name", ["Pylint", "PYLINT"])
def test_supported_case_sensitivity(linter_name):
    """Test check_supported() is case-sensitive and rejects incorrect case."""
    linters = Linters()
    with pytest.raises(ValueError, match="Unsupported linter"):
        linters.check_supported(linter_name)  # Should be 'pylint'


def test_supported_error_message_content():
    """Test error message for unsupported linter includes the linter name."""
    linters = Linters()
    linter_name = "notalinter"
    with pytest.raises(ValueError, match="Unsupported linter") as excinfo:
        linters.check_supported(linter_name)
    assert linter_name in str(excinfo.value)
    assert "Supported" in str(excinfo.value)


# =============================================================================
# 2. Linter availability
# =============================================================================


def test_check_available_found():
    """Test that check_available() passes when linter is found in PATH."""
    linters = Linters()
    with patch("shutil.which", return_value="/usr/bin/pylint"):
        linters.check_available("pylint")  # Should not raise


def test_check_available_not_found():
    """Test that check_available() raises error when linter isn't found."""
    linters = Linters()
    with (
        patch("shutil.which", return_value=None),
        pytest.raises(FileNotFoundError, match="pylint not found"),
    ):
        linters.check_available("pylint")


# =============================================================================
# 3. Linter-specific checks
# =============================================================================


def test_inp001_not_raised(tmp_path):
    """Test INP001 is not raised."""
    skip_if_linter_unexpected("ruff")

    test_dir = Path(__file__).parent
    qmd_source = test_dir / "examples" / "general_example.qmd"

    # Create a subdirectory without __init__.py so INP001 would fire
    subdir = tmp_path / "mypackage"
    subdir.mkdir()

    # .qmd goes in a sub-subdirectory with no __init__.py
    # so the converted .py will be flagged by INP001
    nested = subdir / "scripts"
    nested.mkdir()

    qmd_path = nested / "general_example.qmd"
    qmd_path.write_text(
        qmd_source.read_text(encoding="utf-8"), encoding="utf-8"
    )

    # Add a minimal pyproject.toml so ruff treats this as a project root,
    # making INP001 fire for files in subdirs without __init__.py
    pyproject_toml = subdir / "pyproject.toml"
    pyproject_toml.write_text(
        "[project]\nname = 'test'\nversion = '0.1.0'\n", encoding="utf-8"
    )

    # Write ruff.toml explicitly including INP001
    ruff_toml = subdir / "ruff.toml"
    ruff_toml.write_text('[lint]\nselect = ["INP001"]\n', encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lintquarto",
            "-l",
            "ruff",
            "-p",
            qmd_path,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    output = result.stdout + result.stderr

    assert "INP001" not in output, (
        f"INP001 was raised but should be suppressed by default.\n"
        f"Full output:\n{output}"
    )


def test_ruf100_not_raised(tmp_path):
    """Test RUF100 is not raised."""
    skip_if_linter_unexpected("ruff")

    test_dir = Path(__file__).parent
    qmd_source = test_dir / "examples" / "general_example.qmd"

    qmd_path = tmp_path / "general_example.qmd"
    qmd_path.write_text(
        qmd_source.read_text(encoding="utf-8"), encoding="utf-8"
    )

    # Write ruff.toml explicitly including RUF100
    ruff_toml = tmp_path / "ruff.toml"
    ruff_toml.write_text('[lint]\nselect = ["RUF100"]\n', encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lintquarto",
            "-l",
            "ruff",
            "-p",
            qmd_path,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    output = result.stdout + result.stderr

    assert "RUF100" not in output, (
        f"RUF100 was raised but should be suppressed by default.\n"
        f"Full output:\n{output}"
    )
