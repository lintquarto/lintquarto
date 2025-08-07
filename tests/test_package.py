"""Tests related to package build."""

import subprocess
import sys

import pytest


@pytest.mark.skipif(
    sys.version_info < (3, 8),
    reason="check-dependencies requires Python 3.8+"
)
@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="check-dependencies has known encoding bugs on Windows"
)
def test_check_dependencies():
    """Test for missing or undeclared dependencies."""
    result = subprocess.run(
        ["check-dependencies", "src/lintquarto"],
        capture_output=True, text=True, check=False
    )
    assert result.returncode == 4, (
        "Missing or extra dependencies detected:\n"
        f"{result.stdout}\n{result.stderr}"
    )
