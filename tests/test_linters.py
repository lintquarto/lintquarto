"""
Tests for Linters.
"""

import pytest

from lintquarto.linters import Linters


def test_supported_error():
    """
    Test that check_supported() raises ValueError for unsupported linters.
    """
    linters = Linters()
    with pytest.raises(
        ValueError, match="Unsupported linter 'unsupported_linter'"
    ):
        linters.check_supported("unsupported_linter")


@pytest.mark.parametrize("linter_name", ["pylint", "flake8", "mypy"])
def test_supported_success(linter_name):
    """
    Test that check_supported() returns no errors for supported linters.
    """
    linters = Linters()
    linters.check_supported(linter_name)
