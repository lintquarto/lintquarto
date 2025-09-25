"""Unit tests for the converter module."""

from unittest import mock

import pytest

from lintquarto.converter import (
    convert_qmd_to_py, get_unique_filename, QmdToPyConverter
)

# All linters that preserve the line count
PRESERVE_LINTERS = ["flake8", "mypy", "pycodestyle", "pydoclint", "pyflakes",
                    "pylint", "pyrefly", "pyright", "pytype", "radon-cc",
                    "radon-mi", "radon-hal", "ruff", "vulture"]
LINTERS_SUPPORTING_NOQA = ["flake8", "pycodestyle", "ruff"]


# =============================================================================
# 1. Conversion of files with no active python chunks
# =============================================================================

@pytest.mark.parametrize("linter", PRESERVE_LINTERS)
def test_empty(linter):
    """Empty input produces empty output."""
    converter = QmdToPyConverter(linter=linter)
    assert not converter.convert([])


@pytest.mark.parametrize("linter", PRESERVE_LINTERS)
def test_blank_lines(linter):
    """Blank lines are converted as expected."""
    converter = QmdToPyConverter(linter=linter)
    lines = ["", "", ""]
    expected = ["# -", "# -", "# -"]
    assert converter.convert(lines) == expected


@pytest.mark.parametrize("linter", PRESERVE_LINTERS)
def test_markdown(linter):
    """Markdown lines are commented out."""
    converter = QmdToPyConverter(linter=linter)
    assert converter.convert(["Some text", "More text"]) == ["# -", "# -"]


@pytest.mark.parametrize("linter", PRESERVE_LINTERS)
def test_non_python_chunk_is_commented(linter):
    """Non-Python and inactive chunks are commented out."""
    converter = QmdToPyConverter(linter=linter)
    lines = ["```{r}", "1+1", "```", "```{.python}", "1+1", "```"]
    expected = ["# -", "# -", "# -", "# -", "# -", "# -"]
    assert converter.convert(lines) == expected


# =============================================================================
# 2. Conversion of active python chunks
# =============================================================================

def remove_noqa(lines):
    """
    Helper to remove # noqa comments from expected output

    Parameters
    ----------
    lines : list of str
        Lines of text (expected output)
    """
    return [
        line.split("  # noqa")[0] if "  # noqa" in line
        else line for line in lines
    ]


PYTHON_CHUNKS = [
    {
        "id": "simple code chunk",
        "lines": [
            "```{python}",
            "1+1",
            "```"
        ],
        "expected": [
            "# %% [python]",
            "1+1  # noqa: E305,E501",
            "# -"
        ]
    },
    {
        "id": "function definition",
        "lines": [
            "```{python}",
            "def foo():"
        ],
        "expected": [
            "# %% [python]",
            "def foo():  # noqa: E302,E305,E501"
        ]
    },
    {
        "id": "class definition",
        "lines": [
            "```{python}",
            "class foo:"
        ],
        "expected": [
            "# %% [python]",
            "class foo:  # noqa: E302,E305,E501"
        ]
    },
    {
        "id": "chunk with options and code",
        "lines": [
            "```{python}", " ",
            "#| echo: false",
            "#| output: asis",
            "1+1"
        ],
        "expected": [
            "# %% [python]",
            " ",
            "#| echo: false  # noqa: E265,E501",
            "#| output: asis  # noqa: E265,E501",
            "1+1  # noqa: E305,E501"
        ]
    },
    {
        "id": "indented chunk options",
        "lines": [
            "```{python}",
            "    #| echo: false",
            "    x = 1"
        ],
        "expected": [
            "# %% [python]",
            "    #| echo: false  # noqa: E265,E501",
            "    x = 1  # noqa: E305,E501"
        ]
    },
    {
        "id": "malformed chunk options",
        "lines": [
            "```{python}",
            "#|echo: true",
            " #|   echo: false",
            "# | echo: valid",
            "x = 1",
            "```"],
        "expected": [
            "# %% [python]",
            "#|echo: true",
            " #|   echo: false  # noqa: E265,E501",
            "# | echo: valid",
            "x = 1  # noqa: E305,E501",
            "# -"]
    },
    {
        "id": "multiple consecutive code chunks",
        "lines": [
            "```{python}",
            "a = 1",
            "```",
            "```{python}",
            "b = 2",
            "```"],
        "expected": [
            "# %% [python]",
            "a = 1  # noqa: E305,E501",
            "# -",
            "# %% [python]",
            "b = 2  # noqa: E305,E501",
            "# -"
        ]
    },
    {
        "id": "long line (should omit E501 for long string)",
        "lines": [
            "```{python}",
            "x = '" + "a" * 100 + "'"
        ],
        "expected": [
            "# %% [python]",
            "x = '" + "a" * 100 + "'  # noqa: E305"
        ]
    },
    {
        "id": "first line is a comment",
        "lines": [
            "```{python}",
            "# This is a comment at top of chunk",
            "x = 42"
        ],
        "expected": [
            "# %% [python]",
            "# This is a comment at top of chunk",
            "x = 42  # noqa: E305,E501"
        ]
    },
    {
        "id": "single chunk with include syntax",
        "lines": [
            "```{python}",
            "{{< include filename.py >}}"
        ],
        "expected": [
            "# %% [python]",
            "# {{< include filename.py >}}  # noqa: E305,E501"
        ]
    },
    {
        "id": "comment and code with '#<<' that should be removed",
        "lines": [
            "```{python}",
            "# Comment #<<",
            "variable1 = 2#<<",
            "variable2 = 2   #<<"
        ],
        "expected": [
            "# %% [python]",
            "# Comment",
            "variable1 = 2  # noqa: E305,E501",
            "variable2 = 2"
        ]
    },
    {
        "id": "chunk options and '#<<' that should not be removed",
        "lines": [
            "```{python}",
            "#| echo: false #<<"
        ],
        "expected": [
            "# %% [python]",
            "#| echo: false #<<  # noqa: E265,E501"
        ]
    },
    {
        "id": "chunk options within {python}",
        "lines": [
            "```{python, echo=FALSE}"
        ],
        "expected": [
            "# %% [python]"
        ]
    },
    {
        "id": "spaces before {python}",
        "lines": [
            "```   {python}"
        ],
        "expected": [
            "# %% [python]"
        ]
    }
]


@pytest.mark.parametrize(
    "case", PYTHON_CHUNKS, ids=[c["id"] for c in PYTHON_CHUNKS]
)
@pytest.mark.parametrize("linter", PRESERVE_LINTERS)
def test_python_chunk_start(case, linter):
    """Python chunk conversion produces expected results for all linters."""
    converter = QmdToPyConverter(linter=linter)
    result = converter.convert(case["lines"])
    if linter in LINTERS_SUPPORTING_NOQA:
        assert result == case["expected"]
    else:
        assert result == remove_noqa(case["expected"])
    assert len(result) == len(case["expected"])


def test_line_alignment(tmp_path):
    """Output file has same number of lines as input."""
    input_lines = [
        "Some markdown",
        "```{python}",
        "#| echo: true",
        "",
        "def foo():",
        "    pass",
        "```",
        "More markdown",
        "```{python}",
        "x = 1",
        "```"
    ]
    qmd_file = tmp_path / "input.qmd"
    qmd_file.write_text("\n".join(input_lines))
    result_path = convert_qmd_to_py(qmd_file, "flake8")
    output_lines = result_path.read_text(encoding="utf-8").splitlines()
    assert len(output_lines) == len(input_lines)


# =============================================================================
# 3. Conversion when preserve_line_count = False
# =============================================================================

def test_preserve_line_count_false_removes_non_code():
    """When preserve_line_count is False, non-code lines are skipped."""
    # Simulated .qmd input: markdown, code blocks, and extra blank lines
    qmd_lines = [
        "# This is markdown\n",
        "\n",
        "```{python}",
        "x = 1\n",
        "y = 2\n",
        "```",
        "\n",
        "Some more text\n",
        "```{python}",
        "# comment inside chunk\n",
        "z = x + y\n",
        "```\n"
    ]

    # Create converter with radon-raw (which sets preservation to False - but
    # we do manually anyway for good measure!)
    conv = QmdToPyConverter(linter="radon-raw")
    conv.preserve_line_count = False
    py_lines = conv.convert(qmd_lines)

    # Check there are no filler lines, and only code lines
    expected_lines = [
        "x = 1",
        "y = 2",
        "# comment inside chunk",
        "z = x + y"
    ]
    not_allowed_lines = [
        "# -",
        "# %% [python]"
    ]
    assert py_lines == expected_lines
    assert not any(line.strip() == not_allowed_lines for line in py_lines)
    assert len(py_lines) == 4


# =============================================================================
# 4. File handling and output management
# =============================================================================

def test_get_unique_filename(tmp_path):
    """Generates a unique filename if the file exists."""
    # Create a file named 'test.py'
    file = tmp_path / "test.py"
    file.write_text("content")

    # Call the function to get a unique filename
    unique = get_unique_filename(file)

    # The unique filename should not be the same as the original
    assert unique != file

    # The unique filename should start with 'test (' and end with '.py'
    assert unique.name.startswith("test (")
    assert unique.suffix == ".py"


@pytest.mark.parametrize("linter", PRESERVE_LINTERS)
def test_output_file_overwrite(tmp_path, linter):
    """Uses a unique filename if output file exists."""
    # Create a dummy QMD input file
    qmd_file = tmp_path / "input.qmd"
    qmd_file.write_text("```{python}\n```")

    # Create an output file that already exists
    out_file = tmp_path / "input.py"
    out_file.write_text("existing content")

    # Convert QMD to Python, specifying the output path that already exists
    result_path = convert_qmd_to_py(qmd_file, linter, output_path=out_file)

    # The result should be a new, unique file (not the existing one)
    assert result_path != out_file
    assert result_path.name.startswith("input (")
    assert result_path.suffix == ".py"

    # The new file should contain the expected Python chunk marker
    content = result_path.read_text(encoding="utf-8")
    assert "# %% [python]" in content


@pytest.mark.parametrize("linter", PRESERVE_LINTERS)
def test_verbose_mode_output(tmp_path, capsys, linter):
    """Verbose mode prints progress messages."""
    # Create a minimal QMD input file
    qmd_file = tmp_path / "input.qmd"
    qmd_file.write_text("Some text")

    # Run conversion in verbose mode
    _ = convert_qmd_to_py(qmd_file, linter, verbose=True)

    # Capture printed output
    captured = capsys.readouterr()

    # Check for expected progress messages
    assert "Converting" in captured.out
    assert "Successfully converted" in captured.out
    assert "Line count:" in captured.out


# =============================================================================
# 5. Error handling
# =============================================================================

def test_missing_input_file(tmp_path, capsys):
    """Missing input file prints an error and returns None."""
    result = convert_qmd_to_py(
        "nonexistent.qmd", "flake8", output_path=tmp_path / "out.py"
    )
    captured = capsys.readouterr()
    assert result is None
    assert "Error: Input file 'nonexistent.qmd' not found" in captured.out


def test_permission_error(tmp_path, capsys):
    """PermissionError prints an error and returns None."""
    qmd_file = tmp_path / "input.qmd"
    qmd_file.write_text("``````")
    with mock.patch("builtins.open",
                    side_effect=PermissionError("Mocked permission denied")):
        result = convert_qmd_to_py(
            qmd_file, "flake8", output_path=tmp_path / "out.py"
        )
        captured = capsys.readouterr()
        assert result is None
        assert "Error: Permission denied" in captured.out


def test_general_exception(tmp_path, capsys):
    """Unexpected exception prints error and returns None."""
    with mock.patch("builtins.open",
                    side_effect=RuntimeError("Simulated crash")):
        result = convert_qmd_to_py(
            "input.qmd", "flake8", output_path=tmp_path / "out.py"
        )
        captured = capsys.readouterr()
        assert result is None
        assert "Error during conversion: Simulated crash" in captured.out


def test_unsupported_linter():
    """Unsupported linter name raises an error."""
    with pytest.raises(ValueError):
        QmdToPyConverter(linter="notalinter")
