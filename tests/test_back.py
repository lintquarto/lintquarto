"""Back tests"""

from pathlib import Path
import subprocess
import sys

import pytest

from utils import skip_if_linter_unavailable


TEST_CASES = [
    {
        "linter": "flake8",
        "qmd": "general_example.qmd",
        "contains": [
            "8:80: E501 line too long (98 > 79 characters)",
            "17:1: E305 expected 2 blank lines after class or function",
            "19:1: F401 'sys' imported but unused",
            "E402 module level import not at top of file"
        ]
    },
    {
        "linter": "pycodestyle",
        "qmd": "general_example.qmd",
        "contains": [
            "14:1: E302 expected 2 blank lines, found 0",
            "17:1: E305 expected 2 blank lines after class or function",
            "19:1: E402 module level import not at top of file"
        ]
    },
    {
        "linter": "pydoclint",
        "qmd": "docstring_example.qmd",
        "contains": [
            "8: DOC101: Function `add`: Docstring contains fewer arguments",
            "8: DOC103: Function `add`: Docstring arguments are different",
            "8: DOC201: Function `add` does not have a return section"
        ]
    },
    {
        "linter": "pyflakes",
        "qmd": "general_example.qmd",
        "contains": [
            "19:1: 'sys' imported but unused"
        ]
    },
    {
        "linter": "pylint",
        "qmd": "general_example.qmd",
        "contains": [
            """8:0: C0103: Constant name "very_long_line" doesn't conform """,
            "14:0: C0116: Missing function or method docstring (missing-",
            """19:0: C0413: Import "import sys" should be placed at the """,
            "19:0: W0611: Unused import sys (unused-import)"
        ]
    },
    {
        "linter": "ruff",
        "qmd": "general_example.qmd",
        "contains": [
            "E402 Module level import not at top of file",
            "F401 [*] `sys` imported but unused"
        ]
    },
    {
        "linter": "radon-cc",
        "qmd": "complexity_example.qmd",
        "contains": [
            "F 17:0 check_number - C",
            "F 9:0 simple_addition - A"
        ]
    },
    {
        "linter": "radon-mi",
        "qmd": "complexity_example.qmd",
        "contains": [
            "complexity_example.qmd - A"
        ]
    },
    {
        "linter": "radon-raw",
        "qmd": "lines_example.qmd",
        "contains": [
            "LOC: 10",
            "LLOC: 6",
            "SLOC: 6",
            "Comments: 1",
            "Single comments: 1",
            "Multi: 0",
            "Blank: 3",
            "(C % L): 10%",
            "(C % S): 17%",
            "(C + M % L): 10%"
        ]
    },
    {
        "linter": "radon-hal",
        "qmd": "lines_example.qmd",
        "contains": [
            "h1: 1",
            "h2: 6",
            "N1: 4",
            "N2: 8",
            "vocabulary: 7",
            "length: 12",
            "calculated_length: 15.509775004326936",
            "volume: 33.68825906469125",
            "difficulty: 0.6666666666666666",
            "effort: 22.458839376460833",
            "time: 1.2477132986922685",
            "bugs: 0.011229419688230418"
        ]
    },
    {
        "linter": "vulture",
        "qmd": "unusedcode_example.qmd",
        "contains": [
            "8: unused import 'random' (90% confidence)",
            "10: unused function 'unused_function' (60% confidence)",
            "17: unused variable 'spare_part' (60% confidence)"
        ]
    },
    {
        "linter": "mypy",
        "qmd": "typecheck_example.qmd",
        "contains": [
            """11: error: Argument 2 to "add_numbers" has incompatible """,
            """19: error: Argument 1 to "add_numbers" has incompatible """,
        ]
    },
    {
        "linter": "pyrefly",
        "qmd": "typecheck_example.qmd",
        "contains": [
            "Argument `Literal['5']` is not assignable to parameter `b`",
            "Argument `Literal['apples']` is not assignable to parameter `a`"
        ]
    },
    {
        "linter": "pyright",
        "qmd": "typecheck_example.qmd",
        "contains": [
            '''11:16 - error: Argument of type "Literal['5']" cannot be ''',
            '''19:13 - error: Argument of type "Literal['apples']" cannot '''
        ]
    },
    {
        "linter": "pytype",
        "qmd": "typecheck_example.qmd",
        "contains": [
            # Doesn't include line numbers as different output on python 3.7
            "Function add_numbers was called with the wrong arguments "
        ]
    }
]


@pytest.mark.parametrize(
    "case", TEST_CASES, ids=[case["linter"] for case in TEST_CASES]
)
def test_back_contains(case):
    """Back test checking linter has all messages."""

    skip_if_linter_unavailable(case["linter"])

    test_dir = Path(__file__).parent
    qmd_path = test_dir / "examples" / case["qmd"]

    result = subprocess.run(
        [sys.executable, "-m", "lintquarto",
         "-l", case["linter"], "-p", qmd_path],
        capture_output=True, text=True, check=False
    )
    output = result.stdout + result.stderr

    for expected in case["contains"]:
        assert expected in output, (
            f"Expected '{expected}' to be in output, but it was missing.\n"
            f"Full output:\n{output}"
        )


@pytest.mark.parametrize(
    "case", TEST_CASES, ids=[case["linter"] for case in TEST_CASES]
)
def test_back_file_type(case):
    """Back test checking correct file type in output."""

    skip_if_linter_unavailable(case["linter"])

    test_dir = Path(__file__).parent
    qmd_path = test_dir / "examples" / case["qmd"]

    py_file = case["qmd"].replace(".qmd", ".py")

    result = subprocess.run(
        [sys.executable, "-m", "lintquarto",
         "-l", case["linter"], "-p", qmd_path],
        capture_output=True, text=True, check=False
    )
    output = result.stdout + result.stderr

    assert py_file not in output, (
        f"The filename {py_file} was in output - expected {case['qmd']}.\n"
        f"Full output:\n{output}"
    )

    assert case["qmd"] in output, (
        f"Expected filename {case['qmd']} to be in output, but it was "
        f"missing.\nFull output:\n{output}"
    )
