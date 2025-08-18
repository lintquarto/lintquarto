"""Testing utilities."""

import sys
import pytest


def skip_if_linter_unavailable(linter: str):
    """
    Skips test if the specified linter is not available for the current Python
    version.

    Parameters
    ----------
    linter : str
        Name of linter.
    """
    if linter == "pydoclint" and sys.version_info < (3, 9):
        pytest.skip("pydoclint only supports Python 3.9+")
    if linter == "pytype" and sys.version_info > (3, 12):
        pytest.skip("pytype does not support Python 3.13+")
