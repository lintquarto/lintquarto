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
    # Set yaml as missing - we import yaml and declare dependency pyyaml and
    # that is correct, but check-dependencies does not recognise
    result = subprocess.run(
        ["check-dependencies", "src/lintquarto", "--missing", "yaml"],
        capture_output=True, text=True, check=False
    )
    assert result.returncode in (4, 6), (
        "Missing or extra dependencies detected:\n"
        f"{result.stdout}\n{result.stderr}"
    )
