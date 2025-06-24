"""
Tests for convert_qmd_to_py().
"""

from pathlib import Path
import pytest

from pylintqmd.converter import convert_qmd_to_py


# Test cases
TEST_CASES = [
    {
        "qmd_filename": "simple.qmd",
        "must_contain": [
            "import math",
            "x = 5",
            "def test_func():",
            "return True",
        ],
        "must_not_contain": [
            "title: Test",
            "# This is regular text.",
            "# More text.",
        ],
    },
    {
        "qmd_filename": "mixedcontent.qmd",
        "must_contain": [
            "import math",
            "Test function with docstring.",
            "return x * 2",
            "# Another Python block with potential linting issues",
            "def badfunction(list):"
        ],
        "must_not_contain": [
            "Active R code block",
            "library(base)",
            "# Inactive Python code",
            "This should be commented out",
            "# Inactive R code",
            "This should also be commented out",
            ".callout-note",
            "This is a callout block.",
            ".python-content",
            "This is a custom Python content block.",
            "Some more text content",
            "```{python}",
            "Final text content"
        ],
    }
]


@pytest.mark.parametrize("case", TEST_CASES)
def test_basic_conversion(case, tmp_path):
    """
    Test conversion of various .qmd files with specified string checks.
    """
    # Get the directory of the current test file
    test_dir = Path(__file__).parent
    # Build the paths to the input and output files
    qmd_file = test_dir / f"qmd/{case['qmd_filename']}"
    output_py = tmp_path / "output.py"

    # Check that the test file exists
    assert qmd_file.exists(), f"Test file {qmd_file} does not exist."

    # Convert the file
    convert_qmd_to_py(qmd_path=qmd_file, output_path=output_py)

    # Check that the output file was created
    assert output_py.exists(), f"Output file {output_py} was not created."

    # Load the input .qmd and output .py file
    with open(qmd_file, 'r', encoding='utf-8') as f:
        qmd_content = f.readlines()
    py_content = output_py.read_text(encoding="utf-8")

    # Check that Python blocks are preserved
    for s in case["must_contain"]:
        assert s in py_content, f"Expected '{s}' in output for {qmd_file.name}"

    # Check that non-Python content is commented out
    for s in case["must_not_contain"]:
        assert s not in py_content, (
            f"Did not expect '{s}' in output for {qmd_file.name}")

    # Check line count is preserved (minus one for blank line at end)
    original_lines = len(qmd_content)
    converted_lines = len(py_content.split("\n")) - 1
    assert original_lines == converted_lines
