"""Unit tests for the formatters module."""

from unittest.mock import patch

import pytest

from lintquarto.registry import Formatters

ALL_FORMATTERS = [
    "ruff-format",
    "ruff-format-check",
    "ruff-check-fix",
]

CHECK_ONLY_FORMATTERS = {"ruff-format-check"}


# =============================================================================
# 1. Supported formatters
# =============================================================================


def test_supported_error():
    """Test check_supported() raises ValueError for unsupported formatters."""
    formatters = Formatters()
    with pytest.raises(
        ValueError,
        match="Unsupported formatter 'unsupported_formatter'",
    ):
        formatters.check_supported("unsupported_formatter")


@pytest.mark.parametrize("formatter_name", ALL_FORMATTERS)
def test_supported_success(formatter_name):
    """Test check_supported() returns no errors for supported formatters."""
    formatters = Formatters()
    formatters.check_supported(formatter_name)


@pytest.mark.parametrize("formatter_name", ["", None])
def test_supported_edge_cases(formatter_name):
    """Test check_supported() raises error for empty or None formatter names."""
    formatters = Formatters()
    with pytest.raises(ValueError, match="Unsupported formatter"):
        formatters.check_supported(formatter_name)


@pytest.mark.parametrize("formatter_name", ["Ruff-Format", "RUFF-FORMAT"])
def test_supported_case_sensitivity(formatter_name):
    """Test check_supported() is case-sensitive and rejects incorrect case."""
    formatters = Formatters()
    with pytest.raises(ValueError, match="Unsupported formatter"):
        formatters.check_supported(formatter_name)


# =============================================================================
# 2. Formatter availability
# =============================================================================


def test_check_available_found():
    """Test that check_available() passes when formatter is found in PATH."""
    formatters = Formatters()
    with patch("shutil.which", return_value="/usr/bin/ruff"):
        formatters.check_available("ruff-format")


def test_check_available_not_found():
    """Test that check_available() raises error when formatter isn't found."""
    formatters = Formatters()
    with (
        patch("shutil.which", return_value=None),
        pytest.raises(FileNotFoundError, match="ruff not found"),
    ):
        formatters.check_available("ruff-format")


# =============================================================================
# 3. Formatter commands
# =============================================================================


def test_ruff_format_check_command():
    """Test ruff-format-check maps to the correct command."""
    formatters = Formatters()
    assert formatters.supported["ruff-format-check"] == [
        "ruff",
        "format",
        "--check",
    ]


def test_ruff_format_command():
    """Test ruff-format maps to the correct command."""
    formatters = Formatters()
    assert formatters.supported["ruff-format"] == ["ruff", "format"]


def test_ruff_check_fix_command():
    """Test ruff-check-fix maps to the correct command."""
    formatters = Formatters()
    assert formatters.supported["ruff-check-fix"] == [
        "ruff",
        "check",
        "--fix",
    ]


# =============================================================================
# 4. Check-only formatters
# =============================================================================


def test_check_only_set():
    """Test that check_only formatters are correctly identified."""
    formatters = Formatters()
    assert formatters.check_only == CHECK_ONLY_FORMATTERS


@pytest.mark.parametrize("formatter_name", CHECK_ONLY_FORMATTERS)
def test_check_only_formatter_in_supported(formatter_name):
    """Test that every check-only formatter is also in supported."""
    formatters = Formatters()
    assert formatter_name in formatters.supported


def test_non_check_only_formatters_not_in_check_only():
    """Test that modifying formatters are not in check_only."""
    formatters = Formatters()
    modifying = set(ALL_FORMATTERS) - CHECK_ONLY_FORMATTERS
    for name in modifying:
        assert name not in formatters.check_only
