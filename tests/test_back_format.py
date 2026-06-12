"""Back tests for formatters."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from utils import skip_if_linter_unexpected

FORMATTER_CASES = [
    {
        "formatter": "ruff-format",
        "input": "general_example.qmd",
        "contains": [
            "very_long_line = (",
            '    "This long string exceeds the maximum allowed characters per line."',  # noqa: E501
            "add_numbers(3, 5)",
            "import sys",
        ],
        "not_contains": [
            'very_long_line = "This long string exceeds the maximum allowed characters per line."',  # noqa: E501
        ],
    },
    {
        "formatter": "ruff-check-fix",
        "input": "general_example.qmd",
        "contains": [
            'very_long_line = "This long string exceeds the maximum allowed characters per line."',  # noqa: E501
            "add_numbers(3, 5)",
        ],
        "not_contains": [
            "import sys",
        ],
    },
]


@pytest.mark.parametrize(
    "case",
    FORMATTER_CASES,
    ids=[case["formatter"] for case in FORMATTER_CASES],
)
def test_formatter_rewrites_expected_content(tmp_path, case):
    """Back test checking formatter rewrites QMD as expected."""
    skip_if_linter_unexpected("ruff")

    test_dir = Path(__file__).parent
    src_qmd = test_dir / "examples" / case["input"]
    work_qmd = tmp_path / case["input"]
    shutil.copy(src_qmd, work_qmd)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lintquarto",
            "-f",
            case["formatter"],
            "-p",
            work_qmd,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"Formatter {case['formatter']} failed.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    output_text = work_qmd.read_text(encoding="utf-8")

    for expected in case["contains"]:
        assert expected in output_text, (
            f"Expected '{expected}' in rewritten file for "
            f"{case['formatter']}, but it was missing.\n"
            f"Full file:\n{output_text}"
        )

    for unexpected in case["not_contains"]:
        assert unexpected not in output_text, (
            f"Did not expect '{unexpected}' in rewritten file for "
            f"{case['formatter']}.\n"
            f"Full file:\n{output_text}"
        )
