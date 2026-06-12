"""Convert .qmd file to python file."""

from __future__ import annotations

import traceback
import warnings
from pathlib import Path
from typing import Literal

import tree_sitter_markdown as tsmd
from tree_sitter import Language, Parser

from lintquarto.linelength import LineLengthDetector
from lintquarto.registry import Formatters, Linters

from .build_output import FormatOutputBuilder, LintOutputBuilder
from .collect_python import collect_python_blocks
from .constants import NO_LINE_COUNT_PRESERVATION, SPACING_RULE_LINTERS
from .filename import get_unique_filename
from .parse_yaml import find_metadata_node, parse_yaml_eval_from_node


class QmdToPyConverter:
    """
    Convert lines from a .qmd file to .py file.

    Attributes
    ----------
    lint_non_exec : bool
        If True, also lint non-executable Python code chunks.
    mode : {"lint", "format"}, optional
        Conversion mode. `lint` preserves line alignment for diagnostics.
        `format` emits a formatter-friendly Python file with block separators
        so code can later be spliced back into the original QMD document.
    python_blocks : list[dict]
        List to store metadata for all Python blocks.
    preserve_line_count : bool
        If True, will preserve line alignment.
    spacing_rules : bool
        Whether specified linter reports pycodestyle-style vertical spacing
        checks, such as blank-line errors between top-level functions, classes,
        and methods (e.g., E301, E302, E303, E305, and E306).

    """

    def __init__(
        self,
        tool: str,
        *,
        lint_non_exec: bool = False,
        mode: Literal["lint", "format"] = "lint",
    ) -> None:
        """
        Initialise QmdToPyConverter.

        Parameters
        ----------
        tool : str
            Name of the tool that will be used.
        lint_non_exec : bool, optional
            If True, also lint non-executable Python code chunks.
        mode : Literal["lint", "format"], optional
            Whether to general file suitable for linter or formatter.
        """
        self.lint_non_exec = lint_non_exec
        self.mode = mode

        self.max_line_length = None
        self.python_blocks: list[dict] = []

        # Check the tool is supported
        if self.mode == "lint":
            if tool != "custom":
                Linters().check_supported(tool)
        else:
            Formatters().check_supported(tool)

        # Determine whether to preserve line count
        self.preserve_line_count = (
            self.mode == "lint" and tool not in NO_LINE_COUNT_PRESERVATION
        )

        # Determine if linter needs noqa for spacing rules.
        # If so, find max line length.
        self.spacing_rules = (
            self.mode == "lint" and tool in SPACING_RULE_LINTERS
        )
        if self.spacing_rules:
            len_detect = LineLengthDetector(linter=tool)
            self.max_line_length = len_detect.get_line_length()

    def convert(self, qmd_lines: list[str]) -> list[str]:
        """
        Convert QMD source lines into a lintable Python view.

        This parses the QMD document with Tree-sitter, locates fenced Python
        code blocks, analyses chunk options and YAML front matter, and then
        builds an aligned list of Python lines suitable for a linter.

        In `lint` mode, it will typically produce a line-aligned Python file
        suitable for lint diagnostics. In `format` mode, it produces a compact
        Python file containing only the format-eligible code blocks, separated
        by stable marker comments.

        Parameters
        ----------
        qmd_lines : list of str
            Lines from the input QMD file.

        Returns
        -------
        list of str
            Python lines representing the lintable view of the QMD file.
            Depending on configuration, non-Python regions are replaced by
            placeholder lines so that line numbers stay aligned.
        """
        # Ensure every line ends with `\n` then concatenate all lines into one
        # long string and convert it into bytes, which is the format
        # Tree-sitter expects
        normalized_lines = [
            line if line.endswith("\n") else f"{line}\n" for line in qmd_lines
        ]
        src = "".join(normalized_lines)
        src_bytes = src.encode("utf-8")

        # The parser is the Tree-sitter "machine" that knows the Markdown
        # grammar. We feed the byte sequence into that, and get back a tree
        # object that represents the structure of the document (a syntax tree).
        parser = Parser(Language(tsmd.language()))
        tree = parser.parse(src_bytes)

        # The root node represents the entire document; all other nodes
        # (headings, code blocks, etc.) are children somewhere under this root
        root = tree.root_node

        # Extract YAML front matter metadata, if present
        metadata_node = find_metadata_node(root)
        if metadata_node is not None:
            # Use the YAML to configure the default `execute.eval` behaviour
            yaml_eval_default = parse_yaml_eval_from_node(
                src_bytes, metadata_node
            )
        else:
            # If there is no YAML front matter, fall back to eval=True
            yaml_eval_default = True

        # Find all fenced code blocks where the language is (active or
        # inactive) Python, and collect metadata about them
        self.python_blocks = collect_python_blocks(src_bytes, root)

        # Build the output Python view, line by line, guided by the block
        # metadata extracted above
        if self.mode == "lint":
            output_builder = LintOutputBuilder(
                python_blocks=self.python_blocks,
                lint_non_exec=self.lint_non_exec,
                yaml_eval_default=yaml_eval_default,
                preserve_line_count=self.preserve_line_count,
                spacing_rules=self.spacing_rules,
                max_line_length=self.max_line_length,
            )
        elif self.mode == "format":
            output_builder = FormatOutputBuilder(
                python_blocks=self.python_blocks,
                lint_non_exec=self.lint_non_exec,
                yaml_eval_default=yaml_eval_default,
                preserve_line_count=self.preserve_line_count,
                spacing_rules=self.spacing_rules,
            )

        return output_builder.build(src_bytes)


def convert_qmd_to_py(  # noqa: C901, PLR0913, PLR0912
    qmd_path: str | Path,
    linter: str | None = None,
    formatter: str | None = None,
    output_path: str | Path | None = None,
    *,
    verbose: bool = False,
    lint_non_exec: bool = False,
) -> Path | None:
    """
    Convert Quarto file to Python file, preserving line alignment.

    Parameters
    ----------
    qmd_path : str | Path
        Path to the input .qmd file.
    linter : str
        Name of the linter that will be used.
    formatter : str
        Name of the formatter that will be used.
    output_path : str | Path | None
        Path for the output .py file. If None, uses qmd_path with .py suffix.
    verbose : bool, optional
        If True, print detailed progress information.
    lint_non_exec : bool, optional
        If True, also lint non-executable Python code chunks.

    Returns
    -------
    output_path : Path | None
        Path for the output .py file, or None if there was an error.
    """
    qmd_path = Path(qmd_path)

    if linter is not None and formatter is not None:
        msg = "Provide only one of 'linter' or 'formatter'."
        raise ValueError(msg)

    if formatter is not None:
        tool = formatter
        mode = "format"
    else:
        # lint mode for both real linters and custom commands
        tool = linter if linter is not None else "custom"
        mode = "lint"

    # Set up converter
    converter = QmdToPyConverter(
        tool=tool, lint_non_exec=lint_non_exec, mode=mode
    )

    # Determine output path. If provided, convert to a Path object. If not,
    # the file extension of the input file to `.py`
    if output_path is None:
        output_path = qmd_path.with_suffix(".py")
    else:
        output_path = Path(output_path)

    # Automatically generate a unique filename if needed
    output_path = get_unique_filename(output_path)

    if verbose:
        print(f"Converting {qmd_path} to {output_path}")

    try:
        # Open and read the QMD file, storing all lines in qmd_lines
        with qmd_path.open(encoding="utf-8") as f:
            qmd_lines = f.readlines()

        py_lines = converter.convert(qmd_lines=qmd_lines)

        # Write the output file
        with output_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(py_lines) + "\n")

        if verbose:
            print(f"✓ Successfully converted {qmd_path} to {output_path}")

        # Check that line counts match (if intend to preserve them)
        if converter.preserve_line_count:
            qmd_len = len(qmd_lines)
            py_len = len(py_lines)
            if qmd_len == py_len:
                if verbose:
                    print(f"  Line count: {qmd_len} → {py_len} ")
            else:
                warnings.warn(
                    f"Line count mismatch: {qmd_len} → {py_len}",
                    RuntimeWarning,
                    stacklevel=2,
                )

    # Error messages if issues finding/accessing files, or otherwise.
    except FileNotFoundError:
        print(f"Error: Input file '{qmd_path}' not found")
        return None
    except PermissionError:
        print(
            "Error: Permission denied accessing "
            f"'{qmd_path}' or '{output_path}'"
        )
        return None
    # Intentional broad catch for unexpected conversion errors
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        print(f"Error during conversion: {e}")
        return None

    if formatter is not None:
        return output_path, converter
    return output_path
