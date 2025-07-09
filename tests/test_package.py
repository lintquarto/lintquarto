"""Tests related to package build."""

import subprocess


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
