"""
Tests for convert_qmd_to_py().
"""

from pathlib import Path
import pytest

from lintquarto.converter import convert_qmd_to_py, QmdToPyConverter


# Test cases
TEST_CASES = [
    {
        "qmd_filename": "simple.qmd",
        "py_filename": "simple.py",
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
        "py_filename": "mixedcontent.py",
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
    qmd_file = test_dir / f"examples/{case['qmd_filename']}"
    output_py = tmp_path / "output.py"

    # Check that the test file exists
    assert qmd_file.exists(), f"Test file {qmd_file} does not exist."

    # Convert the file
    convert_qmd_to_py(qmd_path=qmd_file, output_path=output_py)

    # Check that the output file was created
    assert output_py.exists(), f"Output file {output_py} was not created."

    # Load the input .qmd and output .py file
    with open(qmd_file, "r", encoding="utf-8") as f:
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

    # Path to the reference Python file
    reference_py = Path(__file__).parent / f"examples/{case['py_filename']}"

    # Check that the reference file exists
    msg = f"Reference file {reference_py} does not exist."
    assert reference_py.exists(), msg

    # Read both files
    generated_content = output_py.read_text(encoding="utf-8")
    reference_content = reference_py.read_text(encoding="utf-8")

    # Compare their contents
    assert generated_content == reference_content, (
        f"Generated file does not match reference for {case['py_filename']}"
    )


def test_empty():
    """
    Test that empty input returns empty output.
    """
    converter = QmdToPyConverter()
    assert not converter.convert([])


def test_markdown():
    """
    Test that markdown lines are converted to "# -".
    """
    converter = QmdToPyConverter()
    assert converter.convert(["Some text", "More text"]) == ["# -", "# -"]


CHUNK_START_CASES = [
    {
        "lines": ["```{python}",  "1+1", "```"],
        "expected": ["# %% [python]", "1+1  # noqa: E305", "# -"]
    },
    {
        "lines": ["```{python}", "def foo():"],
        "expected": ["# %% [python]", "def foo():  # noqa: E302,E305"]
    },
    {
        "lines": ["```{python}", "class foo:"],
        "expected": ["# %% [python]", "class foo:  # noqa: E302,E305"]
    }
]


@pytest.mark.parametrize("case", CHUNK_START_CASES)
def test_python_chunk_start(case):
    """
    Test that Python chunk start if converted correctly.
    """
    converter = QmdToPyConverter()
    assert converter.convert(case["lines"]) == case["expected"]


def test_chunk_options():
    """
    Test that cells with chunk options at start are amended correctly.
    """
    converter = QmdToPyConverter()
    lines = ["```{python}", " ", "#| echo: false", "#| output: asis", "1+1"]
    expected = ["# %% [python]", " ", "# |echo: false", "# |output: asis",
                "1+1  # noqa: E305"]
    assert converter.convert(lines) == expected
