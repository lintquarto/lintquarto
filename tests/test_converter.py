"""Unit tests for the converter module."""

from pathlib import Path
from unittest import mock

import pytest
import tree_sitter_markdown as tsmd
from tree_sitter import Language, Parser

from lintquarto.converter import (
    QmdToPyConverter,
    convert_qmd_to_py,
    get_unique_filename,
)

# All linters that preserve the line count
PRESERVE_LINTERS = [
    "flake8",
    "mypy",
    "pycodestyle",
    "pydoclint",
    "pyflakes",
    "pylint",
    "pyrefly",
    "pyright",
    "pytype",
    "radon-cc",
    "radon-mi",
    "radon-hal",
    "ruff",
    "vulture",
]
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
    # Still keep [python] but not cell contents (consistent with eval=False)
    converter = QmdToPyConverter(linter=linter)
    lines = ["```{r}", "1+1", "```", "```{.python}", "1+1", "```"]
    expected = ["# -", "# -", "# -", "# %% [python]", "# -", "# -"]
    assert converter.convert(lines) == expected


# =============================================================================
# 2. Conversion of active python chunks
# =============================================================================


def remove_noqa(lines: list[str]) -> list[str]:
    """
    Remove noqa comments from expected output.

    Parameters
    ----------
    lines : list[str]
        Lines of text (expected output)

    Returns
    -------
    list[str]
        Lines with any trailing '  noqa: ...' comments removed.

    """
    return [
        line.split("  # noqa")[0] if "  # noqa" in line else line
        for line in lines
    ]


PYTHON_CHUNKS = [
    {
        "id": "simple code chunk",
        "lines": [
            "```{python}",
            "1+1",
            "```",
        ],
        "expected": [
            "# %% [python]",
            "1+1  # noqa: E305,E501",
            "# -",
        ],
    },
    {
        "id": "function definition",
        "lines": [
            "```{python}",
            "def foo():",
        ],
        "expected": [
            "# %% [python]",
            "def foo():  # noqa: E302,E305,E501",
        ],
    },
    {
        "id": "class definition",
        "lines": [
            "```{python}",
            "class foo:",
        ],
        "expected": [
            "# %% [python]",
            "class foo:  # noqa: E302,E305,E501",
        ],
    },
    {
        "id": "chunk with options and code",
        "lines": [
            "```{python}",
            " ",
            "#| echo: false",
            "#| output: asis",
            "1+1",
        ],
        "expected": [
            "# %% [python]",
            " ",
            "# -",
            "# -",
            "1+1  # noqa: E305,E501",
        ],
    },
    {
        "id": "indented chunk options",
        "lines": [
            "```{python}",
            "    #| echo: false",
            "    x = 1",
        ],
        "expected": [
            "# %% [python]",
            "# -",
            "    x = 1  # noqa: E305,E501",
        ],
    },
    {
        "id": "malformed chunk options are unhandled",
        "lines": [
            "```{python}",
            "#|echo: true",
            "# | echo: valid",
            "x = 1",
            "```",
        ],
        "expected": [
            "# %% [python]",
            "#|echo: true",
            "# | echo: valid",
            "x = 1  # noqa: E305,E501",
            "# -",
        ],
    },
    {
        "id": "multiple consecutive code chunks",
        "lines": [
            "```{python}",
            "a = 1",
            "```",
            "```{python}",
            "b = 2",
            "```",
        ],
        "expected": [
            "# %% [python]",
            "a = 1  # noqa: E305,E501",
            "# -",
            "# %% [python]",
            "b = 2  # noqa: E305,E501",
            "# -",
        ],
    },
    {
        "id": "long line (should omit E501 for long string)",
        "lines": [
            "```{python}",
            "x = '" + "a" * 100 + "'",
        ],
        "expected": [
            "# %% [python]",
            "x = '" + "a" * 100 + "'  # noqa: E305",
        ],
    },
    {
        "id": "first line is a comment",
        "lines": [
            "```{python}",
            "# This is a comment at top of chunk",
            "x = 42",
        ],
        "expected": [
            "# %% [python]",
            "# This is a comment at top of chunk",
            "x = 42  # noqa: E305,E501",
        ],
    },
    {
        "id": "single chunk with include syntax",
        "lines": [
            "```{python}",
            "{{< include filename.py >}}",
        ],
        "expected": [
            "# %% [python]",
            "# {{< include filename.py >}}  # noqa: E305,E501",
        ],
    },
    {
        "id": "comment and code with '#<<' that should be removed",
        "lines": [
            "```{python}",
            "# Comment #<<",
            "variable1 = 2#<<",
            "variable2 = 2   #<<",
        ],
        "expected": [
            "# %% [python]",
            "# Comment",
            "variable1 = 2  # noqa: E305,E501",
            "variable2 = 2",
        ],
    },
    {
        "id": "chunk options and '#<<'",
        "lines": [
            "```{python}",
            "#| echo: false #<<",
        ],
        "expected": [
            "# %% [python]",
            "# -",
        ],
    },
    {
        "id": "code annotations '# <n>' removed like '#<<'",
        "lines": [
            "```{python}",
            "# Comment # <1>",
            "value = 1# <2>",
            "value = 2   # <10>",
        ],
        "expected": [
            "# %% [python]",
            "# Comment",
            "value = 1  # noqa: E305,E501",
            "value = 2",
        ],
    },
    {
        "id": "chunk options and '# <n>'",
        "lines": [
            "```{python}",
            "#| echo: false # <1>",
        ],
        "expected": [
            "# %% [python]",
            "# -",
        ],
    },
    {
        "id": "chunk options within {python}",
        "lines": [
            "```{python, echo=FALSE}",
        ],
        "expected": [
            "# %% [python]",
        ],
    },
    {
        "id": "spaces before {python}",
        "lines": [
            "```   {python}",
        ],
        "expected": [
            "# %% [python]",
        ],
    },
]


@pytest.mark.parametrize(
    "case",
    PYTHON_CHUNKS,
    ids=[c["id"] for c in PYTHON_CHUNKS],
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
        "```",
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
        "```\n",
    ]

    # Create converter with radon-raw (which sets preservation to False - but
    # we do manually anyway for good measure!)
    conv = QmdToPyConverter(linter="radon-raw")
    conv.preserve_line_count = False
    _ = conv.preserve_line_count  # reassure static tools
    py_lines = conv.convert(qmd_lines)

    # Check there are no filler lines, and only code lines
    expected_lines = [
        "x = 1",
        "y = 2",
        "# comment inside chunk",
        "z = x + y",
    ]
    not_allowed_lines = [
        "# -",
        "# %% [python]",
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

    # The unique filename should start with 'test_' and end with '.py'
    assert unique.name.startswith("test_")
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
    assert result_path.name.startswith("input_")
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
        "nonexistent.qmd",
        "flake8",
        output_path=tmp_path / "out.py",
    )
    captured = capsys.readouterr()
    assert result is None
    assert "Error: Input file 'nonexistent.qmd' not found" in captured.out


def test_permission_error(tmp_path, capsys):
    """PermissionError prints an error and returns None."""
    qmd_file = tmp_path / "input.qmd"
    qmd_file.write_text("``````")
    with mock.patch.object(
        Path,
        "open",
        side_effect=PermissionError("Mocked permission denied"),
    ):
        result = convert_qmd_to_py(
            qmd_file,
            "flake8",
            output_path=tmp_path / "out.py",
        )
        captured = capsys.readouterr()
        assert result is None
        assert "Error: Permission denied" in captured.out


def test_general_exception(tmp_path, capsys):
    """Unexpected exception prints error and returns None."""
    with mock.patch.object(
        Path,
        "open",
        side_effect=RuntimeError("Simulated crash"),
    ):
        result = convert_qmd_to_py(
            "input.qmd",
            "flake8",
            output_path=tmp_path / "out.py",
        )
        captured = capsys.readouterr()
        assert result is None
        assert "Error during conversion: Simulated crash" in captured.out


def test_unsupported_linter():
    """Unsupported linter name raises an error."""
    with pytest.raises(ValueError, match="Unsupported linter"):
        QmdToPyConverter(linter="notalinter")


# =============================================================================
# 6. _parse_yaml_eval_from_node()
# =============================================================================


def _parse_root(lines: list[str]):
    """Parse lines with the markdown parser and return root + bytes."""
    normalized_lines = [
        line if line.endswith("\n") else f"{line}\n" for line in lines
    ]
    src = "".join(normalized_lines)
    src_bytes = src.encode("utf-8")
    parser = Parser(Language(tsmd.language()))
    tree = parser.parse(src_bytes)
    return src_bytes, tree.root_node


@pytest.mark.parametrize(
    ("lines", "expected_eval"),
    [
        (
            # No YAML at all → default True
            ["# title\n", "```{python}\n"],
            True,
        ),
        (
            # Proper YAML with execute.eval: false
            [
                "---\n",
                "title: Test\n",
                "execute:\n",
                "  eval: false\n",
                "---\n",
                "```{python}\n",
            ],
            False,
        ),
        (
            # execute present but eval missing → default True
            [
                "---\n",
                "execute:\n",
                "  echo: true\n",
                "---\n",
                "```{python}\n",
            ],
            True,
        ),
        (
            # Non-dict execute → ignore, default True
            [
                "---\n",
                "execute: false\n",
                "---\n",
                "```{python}\n",
            ],
            True,
        ),
        (
            # String variant, case-insensitive
            [
                "---\n",
                "execute:\n",
                '  eval: "False"\n',
                "---\n",
            ],
            False,
        ),
        (
            # Unclosed YAML (no trailing ---) → treated as no YAML
            [
                "---\n",
                "title: bad\n",
                "execute:\n",
                "  eval: false\n",
                "# no closing fence\n",
            ],
            True,
        ),
    ],
    ids=[
        "no_yaml",
        "yaml_eval_false",
        "execute_without_eval",
        "execute_not_dict",
        "yaml_eval_string_false",
        "yaml_unclosed",
    ],
)
def test_parse_yaml_eval_from_node(lines, expected_eval):
    """Unit: YAML front matter is interpreted with expected eval default."""
    converter = QmdToPyConverter(linter="flake8")
    src_bytes, root = _parse_root(lines)
    metadata_node = converter._find_metadata_node(root)

    if metadata_node is None:
        actual = True
    else:
        actual = converter._parse_yaml_eval_from_node(src_bytes, metadata_node)

    assert actual is expected_eval


def test_parse_yaml_eval_from_node_invalid_yaml():
    """Unit: Invalid YAML should fall back to default eval=True."""
    lines = [
        "---\n",
        "title: [unclosed\n",
        "---\n",
    ]
    converter = QmdToPyConverter(linter="flake8")
    src_bytes, root = _parse_root(lines)
    metadata_node = converter._find_metadata_node(root)
    assert metadata_node is not None
    assert (
        converter._parse_yaml_eval_from_node(src_bytes, metadata_node) is True
    )


# =============================================================================
# 7. _parse_chunk_eval()
# =============================================================================


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("#| eval: true", True),
        ("#| eval: false", False),
        ("#| eval: TRUE", True),
        ("#| eval: FALSE", False),
        ("#| eval: 'true'", True),
        ('#| eval: "false"', False),
        ("#|   eval  :   yes", True),
        ("#| eval: 0", False),
        ("#| other: true", None),
        ("#| eval : maybe", None),
    ],
    ids=[
        "true",
        "false",
        "upper_true",
        "upper_false",
        "quoted_true",
        "quoted_false",
        "yes",
        "zero",
        "no_eval_key",
        "invalid_value",
    ],
)
def test_parse_chunk_eval(line, expected):
    """Unit: _parse_chunk_eval parses boolean eval values."""
    converter = QmdToPyConverter(linter="flake8")
    stripped = line.lstrip()
    option_text = (
        stripped[3:].strip() if stripped.startswith("#| ") else stripped
    )
    assert (
        converter._parse_chunk_eval(option_text, current_eval=None) is expected
    )


def test_parse_chunk_eval_preserves_current_when_no_eval_key():
    """Unit: Leaves current value unchanged if no eval key."""
    converter = QmdToPyConverter(linter="flake8")
    assert (
        converter._parse_chunk_eval("other: true", current_eval=True) is True
    )
    assert (
        converter._parse_chunk_eval("echo: false", current_eval=False) is False
    )


# =============================================================================
# 8. Integration: eval controls which chunks are kept
# =============================================================================


def _convert(
    lines,
    *,  # Subsequent arguments are keyword-only (`var=True`, not just `True`)
    lint_non_exec=False,
):
    conv = QmdToPyConverter(linter="flake8", lint_non_exec=lint_non_exec)
    return conv.convert(lines)


def test_no_yaml_all_chunks_linted_by_default():
    """Integration: no YAML → all python chunks linted (kept)."""
    qmd = [
        "Some text\n",
        "```{python}\n",
        "x = 1\n",
        "```\n",
        "\n",
        "```{python}\n",
        "y = 2\n",
        "```\n",
    ]
    py = _convert(qmd)
    assert any("x = 1" in line for line in py)
    assert any("y = 2" in line for line in py)
    assert len(py) == len(qmd)


def test_yaml_eval_false_lint_non_exec_false():
    """Integration: YAML eval: false → all chunks skipped unless overridden."""
    qmd = [
        "---\n",
        "execute:\n",
        "  eval: false\n",
        "---\n",
        "\n",
        "```{python}\n",
        "x = 1\n",
        "```\n",
    ]
    py = _convert(qmd)
    assert "x = 1" not in py
    # still preserving line count
    assert len(py) == len(qmd)


def test_yaml_eval_false_lint_non_exec_true():
    """Integration: YAML eval: false but lint-non-exec=True."""
    qmd = [
        "---\n",
        "execute:\n",
        "  eval: false\n",
        "---\n",
        "\n",
        "```{python}\n",
        "x = 1\n",
        "```\n",
    ]
    py = _convert(qmd, lint_non_exec=True)
    assert any("x = 1" in line for line in py)
    assert len(py) == len(qmd)


def test_chunk_eval_true_overrides_yaml_false():
    """Integration: #| eval: true keeps chunk even if YAML eval: false."""
    qmd = [
        "---\n",
        "execute:\n",
        "  eval: false\n",
        "---\n",
        "\n",
        "```{python}\n",
        "#| eval: true\n",
        "x = 1\n",
        "```\n",
    ]
    py = _convert(qmd)
    assert any("x = 1" in line for line in py)


def test_chunk_eval_false_overrides_yaml_true():
    """Integration: #| eval: false skips chunk even if YAML eval: true."""
    qmd = [
        "---\n",
        "execute:\n",
        "  eval: true\n",
        "---\n",
        "\n",
        "```{python}\n",
        "#| eval: false\n",
        "x = 1\n",
        "```\n",
    ]
    py = _convert(qmd)
    assert "x = 1" not in py


def test_chunk_eval_false_without_yaml():
    """Integration: #| eval: false skips chunk when no YAML present."""
    qmd = [
        "```{python}\n",
        "#| eval: false\n",
        "x = 1\n",
        "```\n",
    ]
    py = _convert(qmd)
    assert "x = 1" not in py
    assert len(py) == len(qmd)


def test_chunk_eval_false_kept_when_include_non_exec():
    """Integration: #| eval: false chunk kept when include_non_exec=True."""
    qmd = [
        "```{python}\n",
        "#| eval: false\n",
        "x = 1\n",
        "```\n",
    ]
    py = _convert(qmd, lint_non_exec=True)
    assert any("x = 1" in line for line in py)
    assert len(py) == len(qmd)


def test_yaml_eval_false_chunk_eval_false_both_kept_when_include_non_exec():
    """Integration: YAML eval:false + chunk eval:false still kept with flag."""
    qmd = [
        "---\n",
        "execute:\n",
        "  eval: false\n",
        "---\n",
        "\n",
        "```{python}\n",
        "#| eval: false\n",
        "x = 1\n",
        "```\n",
    ]
    py = _convert(qmd, lint_non_exec=True)
    assert any("x = 1" in line for line in py)
    assert len(py) == len(qmd)


def test_inactive_lint_non_exec():
    """Integration: {.python} linted if lint_non_exec=True."""
    qmd = [
        "```{.python}\n",
        "x = 1\n",
        "```\n",
    ]
    py = _convert(qmd, lint_non_exec=True)
    assert any("x = 1" in line for line in py)


def test_multiple_chunk_options():
    """Integration: other options (#| echo etc.) must not reset eval."""
    qmd = [
        "```{python}\n",
        "#| eval: true\n",
        "#| echo: false\n",
        "#| warning: false\n",
        "x = 1\n",
        "```\n",
    ]
    py = _convert(qmd)
    assert any("x = 1" in line for line in py)


def test_chunk_eval_option_order_irrelevant():
    """Integration: eval can appear before or after other options."""
    qmd = [
        "```{python}\n",
        "#| echo: false\n",
        "#| eval: true\n",
        "x = 1\n",
        "```\n",
    ]
    py = _convert(qmd)
    assert any("x = 1" in line for line in py)


def test_chunk_eval_resets_between_chunks():
    """Integration: eval setting must not bleed into next chunk."""
    qmd = [
        "```{python}\n",
        "#| eval: false\n",
        "x = 1\n",
        "```\n",
        "\n",
        "```{python}\n",
        "y = 2\n",
        "```\n",
    ]
    py = _convert(qmd)
    # first chunk skipped
    assert "x = 1" not in py
    # second chunk uses default (True when no YAML)
    assert any("y = 2" in line for line in py)


def test_yaml_eval_false_with_mixed_chunks():
    """Integration: YAML eval: false with one chunk overriding to true."""
    qmd = [
        "---\n",
        "execute:\n",
        "  eval: false\n",
        "---\n",
        "\n",
        "```{python}\n",
        "a = 1\n",
        "```\n",
        "\n",
        "```{python}\n",
        "#| eval: true\n",
        "b = 2\n",
        "```\n",
        "\n",
        "```{python}\n",
        "c = 3\n",
        "```\n",
    ]
    py = _convert(qmd)
    assert "a = 1" not in py
    assert "c = 3" not in py
    assert any("b = 2" in line for line in py)


def test_yaml_eval_false_comments_code():
    """Integration: in eval: false chunk, comments + code become non-code."""
    qmd = [
        "```{python}\n",
        "#| eval: false\n",
        "# a comment\n",
        "x = 1\n",
        "```\n",
    ]
    py = _convert(qmd)
    assert "# a comment" not in py
    assert "x = 1" not in py
    assert len(py) == len(qmd)


def test_yaml_eval_false_skip_exercise():
    """Integration: setup linted, exercise chunks skipped."""
    qmd = [
        "---\n",
        "execute:\n",
        "  eval: false\n",
        "---\n",
        "\n",
        "# Setup\n",
        "```{python}\n",
        "#| eval: true\n",
        "import math\n",
        "x = 1\n",
        "```\n",
        "\n",
        "# Exercise\n",
        "```{python}\n",
        "y = x + 1\n",
        "```\n",
    ]
    py = _convert(qmd)
    # Setup kept
    assert any("import math" in line for line in py)
    assert any("x = 1" in line for line in py)
    # Exercise skipped
    assert not any("y = x + 1" in line for line in py)


def test_yaml_eval_false_plain_chunk():
    """Integration: YAML eval=false, 1st chunk plain, 2nd eval:true."""
    qmd = [
        "---\n",
        "title: Example\n",
        "execute:\n",
        "  eval: false\n",
        "---\n",
        "\n",
        "Some text\n",
        "\n",
        "```{python}\n",
        "a = 1\n",
        "b = 2\n",
        "```\n",
        "\n",
        "More text\n",
        "\n",
        "```{python}\n",
        "#| eval: true\n",
        "c = 3\n",
        "d = 4\n",
        "```\n",
    ]

    py = _convert(qmd)

    # First chunk (no #| eval, YAML eval:false) should be completely skipped
    assert "a = 1" not in py
    assert "b = 2" not in py

    # Second chunk (eval:true) should be present
    assert any("c = 3" in line for line in py)
    assert any("d = 4" in line for line in py)

    # Line count preserved
    assert len(py) == len(qmd)


# =============================================================================
# 9. valuebox
# =============================================================================


@pytest.mark.parametrize(
    "content_valuebox",
    [
        "#| content: valuebox",
        "  #| content: valuebox",
        "#| content: valuebox  ",
    ],
)
def test_valuebox_ignored(content_valuebox):
    """Quarto valuebox cells should be commented out."""
    qmd = [
        "```{python}\n",
        f"{content_valuebox}\n",
        "#| title: 'Comments per day'\n",
        "dict(\n",
        "  icon = 'chat'\n",
        "  color = 'primary'\n",
        "  value = comments\n",
        ")\n",
        "```",
    ]
    expected = [
        "# %% [python]",
        "# -",
        "# -",
        "# -",
        "# -",
        "# -",
        "# -",
        "# -",
        "# -",
    ]
    py = _convert(qmd)
    assert py == expected
