"""Unit tests for the linters module."""

from unittest.mock import patch

import pytest

from lintquarto.linters import Linters


ALL_LINTERS = ["flake8", "mypy", "pycodestyle", "pydoclint", "pyflakes",
               "pylint", "pyrefly", "pyright", "pytype", "radon-cc",
               "radon-mi", "radon-raw", "radon-hal", "ruff", "vulture"]


# =============================================================================
# 1. Supported linters
# =============================================================================

def test_supported_error():
    """
    Test that check_supported() raises ValueError for unsupported linters.
    """
    linters = Linters()
    with pytest.raises(
        ValueError, match="Unsupported linter 'unsupported_linter'"
    ):
        linters.check_supported("unsupported_linter")


@pytest.mark.parametrize("linter_name", ALL_LINTERS)
def test_supported_success(linter_name):
    """
    Test that check_supported() returns no errors for supported linters.
    """
    linters = Linters()
    linters.check_supported(linter_name)


@pytest.mark.parametrize("linter_name", ["", None])
def test_supported_edge_cases(linter_name):
    """
    Test that check_supported() raises error for empty or None linter names.
    """
    linters = Linters()
    with pytest.raises(ValueError):
        linters.check_supported(linter_name)


@pytest.mark.parametrize("linter_name", ["Pylint", "PYLINT"])
def test_supported_case_sensitivity(linter_name):
    """
    Test that check_supported() is case-sensitive and rejects incorrect case.
    """
    linters = Linters()
    with pytest.raises(ValueError):
        linters.check_supported(linter_name)  # Should be 'pylint'


def test_supported_error_message_content():
    """
    Test that error message for unsupported linter includes the linter name.
    """
    linters = Linters()
    linter_name = "notalinter"
    with pytest.raises(ValueError) as excinfo:
        linters.check_supported(linter_name)
    assert linter_name in str(excinfo.value)
    assert "Supported" in str(excinfo.value)


# =============================================================================
# 2. Linter availability
# =============================================================================

def test_check_available_found():
    """
    Test that check_available() passes when linter is found in PATH.
    """
    linters = Linters()
    with patch("shutil.which", return_value="/usr/bin/pylint"):
        linters.check_available("pylint")  # Should not raise


def test_check_available_not_found():
    """
    Test that check_available() raises error when linter isn't found.
    """
    linters = Linters()
    with patch("shutil.which", return_value=None):
        with pytest.raises(FileNotFoundError, match="pylint not found"):
            linters.check_available("pylint")
