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
    if linter == "pytype" and sys.version_info >= (3, 13):
        pytest.skip("pytype does not support Python 3.13+")
