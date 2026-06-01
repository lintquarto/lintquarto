"""Unit tests for the linters module."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from utils import skip_if_linter_unexpected

from lintquarto.linters import Linters

ALL_LINTERS = [
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


def test_finds_most_local_ruff_config():
    """Check that expected ruff config is found.

    Checks that for a qmd with a ruff.toml in the same folder, this
    is given preference over a file living several folders up, and
    also prefers ruff.toml over pyproject.toml
    """
    test_dir = Path(__file__).parent
    qmd_path = test_dir / "examples_config_ruff_valid" / "general_example.qmd"
    expected = test_dir / "examples_config_ruff_valid" / "ruff.toml"
    linters = Linters()
    ruff_config = linters.ruff_has_config(qmd_path, return_path=True)
    assert ruff_config == expected, f"Expected {expected}, got: {ruff_config}"


def test_ignores_invalid_ruff_pyproject_toml_config():
    """Check malformed pyproject.toml will be ignored.

    If a pyproject.toml is incorrectly formatted (missing [tool.ruff])
    then the tree searcher should keep looking.
    """
    test_dir = Path(__file__).parent
    qmd_path = (
        test_dir / "examples_config_ruff_invalid" / "general_example.qmd"
    )
    expected = test_dir.parent / "pyproject.toml"
    linters = Linters()
    ruff_config = linters.ruff_has_config(qmd_path, return_path=True)
    assert ruff_config == expected, f"Expected {expected}, got: {ruff_config}"


def test_finds_distant_ruff_config():
    """
    Checks that ruff config files in other folders are found.

    Checks that ruff correctly looks upwards through the tree
    until it finds a valid ruff file.
    """
    test_dir = Path(__file__).parent
    qmd_path = test_dir / "examples" / "general_example.qmd"
    expected = test_dir.parent / "pyproject.toml"
    linters = Linters()
    ruff_config = linters.ruff_has_config(qmd_path, return_path=True)
    assert ruff_config == expected, f"Expected {expected}, got: {ruff_config}"


def test_docstring_example_no_unused_noqa_by_default(tmp_path):
    """Test default ruff exclusions work."""
    skip_if_linter_unexpected("ruff")

    test_dir = Path(__file__).parent
    qmd_source = test_dir / "examples" / "general_example.qmd"

    # Copy the .qmd file to an isolated temporary directory
    # Walking up from here will hit the system temp root, finding
    # no pyproject.toml wheras if we run it directly from the true path,
    # it finds the pyproject.toml used for the library, resulting in
    # unexpected behaviour in this test
    qmd_path = tmp_path / "general_example.qmd"
    qmd_path.write_text(
        qmd_source.read_text(encoding="utf-8"), encoding="utf-8"
    )

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

    print(output)

    expected = [
        "E402 Module level import not at top of file",
        "F401 [*] `sys` imported but unused",
    ]

    # Check all anticipated messages appear
    for expected_message in expected:
        assert expected_message in output, (
            f"Expected '{expected_message}' to be in output,"
            "but it was missing.\n"
            f"Full output:\n{output}"
        )

    # Check that a known error that would otherwise appear
    # if not in default exclusions definitely appears
    assert "Unused `noqa` directive" not in output, (
        f"Unexpected unused-noqa warning found:\n{output}"
    )


def test_ruff_config_addition(tmp_path):
    """Check that user-provided ruff config overrides default exclusions."""
    skip_if_linter_unexpected("ruff")

    test_dir = Path(__file__).parent
    qmd_source = (
        test_dir / "examples_config_ruff_valid" / "general_example.qmd"
    )
    config_source = test_dir / "examples_config_ruff_valid" / "ruff.toml"

    # Copy the .qmd file and config file to an isolated temporary directory
    # to avoid any unexpected behaviour
    qmd_path = tmp_path / "general_example.qmd"
    qmd_path.write_text(
        qmd_source.read_text(encoding="utf-8"), encoding="utf-8"
    )

    config_path = tmp_path / "ruff.toml"
    config_path.write_text(
        config_source.read_text(encoding="utf-8"), encoding="utf-8"
    )

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

    unexpected = [
        "F401 [*] `sys` imported but unused",
    ]

    expected = [
        "E402 Module level import not at top of file",
        # Crucially, 'unused `noqa` directive' should appear
        # because the provided config file should override the defaults
        # that are passed in and therefore  the usual ignored errors
        # should be thrown
        "Unused `noqa` directive",
    ]

    for unexpected_message in unexpected:
        assert unexpected_message not in output, (
            f"Expected '{unexpected_message}' to not be present in output,"
            "but it was present.\n"
            f"Full output:\n{output}"
        )

    for expected_message in expected:
        assert expected_message in output, (
            f"Expected '{expected_message}' to be in output, "
            "but it was missing.\n"
            f"Full output:\n{output}"
        )
