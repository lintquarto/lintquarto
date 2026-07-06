"""Test formatter behaviour."""

import subprocess
import sys


def test_import_sort(tmp_path):
    """Confirm that ruff-check-fix import sorting behaves correctly."""

    qmd_path = tmp_path / "imports.qmd"
    qmd_path.write_text(
        (
            "```{python}\n"
            "import arrow\n"
            "from rich import print\n"
            "```\n"
            "```{python}\n"
            "past = arrow.utcnow().shift(hours=-1)\n"
            """print(f"One hour ago was {past.humanize()}.")\n"""
            "```"
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lintquarto",
            "-f",
            "ruff-check-fix",
            "-p",
            qmd_path,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    assert "I001" not in output, (
        f"I001 was raised by ruff check fix but should have been resolved.\n"
        f"Full output:\n{output}"
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
    assert "I001" not in output, (
        f"I001 was raised by ruff check but should have been resolved.\n"
        f"Full output:\n{output}"
    )
