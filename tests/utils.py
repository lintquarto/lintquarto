"""Testing utilities."""

import sys

import pytest


def _is_linter_expected(linter: str):
    """Return True if linter is expected on this Python version."""
    if linter == "pytype" and sys.version_info >= (3, 13):
        return False
    return True


def skip_if_linter_unexpected(linter: str):
    """
    Skips test if linter is not expected for the current Python version.

    Parameters
    ----------
    linter : str
        Name of linter.

    """
    if not _is_linter_expected(linter):
        pytest.skip("pytype does not support Python 3.13+")
