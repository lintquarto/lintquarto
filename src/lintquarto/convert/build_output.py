"""Build the Python output from block metadata."""

import re
from typing import Any

from .constants import FORMAT_SEPARATOR_PREFIX


class OutputBuilder:
    """
    Base class for building Python output from parsed document metadata.

    Contains methods shared by LintOutputBuilder and FormatOutputBuilder.

    Attributes
    ----------
    python_blocks : list[dict]
        Metadata for Python code blocks.
    lint_non_exec : bool
        Whether to lint non-executed chunks.
    yaml_eval_default : bool
        Document-level default for execute.eval.
    preserve_line_count : bool
        Whether to preserve source line count in the output.
    spacing_rules : bool
        Whether to add noqa spacing suppressions for lint output.
    py_lines : list[str]
        Output buffer to populate.
    """

    def __init__(
        self,
        python_blocks: list[dict],
        *,
        lint_non_exec: bool,
        yaml_eval_default: bool,
        preserve_line_count: bool,
        spacing_rules: bool,
    ) -> None:
        """
        Initialise OutputBuilder.

        Parameters
        ----------
        python_blocks : list[dict]
            Metadata for Python code blocks.
        lint_non_exec : bool
            Whether to lint non-executed chunks.
        yaml_eval_default : bool
            Document-level default for execute.eval.
        preserve_line_count : bool
            Whether to preserve source line count in the output.
        spacing_rules : bool
            Whether to add noqa spacing suppressions for lint output.
        """
        self.python_blocks = python_blocks
        self.lint_non_exec = lint_non_exec
        self.yaml_eval_default = yaml_eval_default
        self.preserve_line_count = preserve_line_count
        self.spacing_rules = spacing_rules

        self.py_lines = []

    def should_process_block(self, block: dict) -> bool:
        """
        Determine whether a given Python block should be processed.

        This combines global settings (`lint_non_exec`), the block's
        active/inactive status, any chunk-level `eval` options, and the
        default YAML `execute.eval` value.

        Parameters
        ----------
        block : dict
            Metadata dictionary describing a Python code block.

        Returns
        -------
        bool
            `True` if the block should be included in linting, `False`
            otherwise.
        """
        # If configured to lint all chunks, ignore eval/inactive flags
        if self.lint_non_exec:
            return True

        # Inactive chunks only get linted if they explicitly set eval.
        if block["is_inactive"]:
            return (
                block["chunk_eval"]
                if block["chunk_eval"] is not None
                else False
            )
        if block["chunk_eval"] is not None:
            return block["chunk_eval"]

        # Fallback: use the document-wide default.
        return self.yaml_eval_default

    def handle_includes(self, line: str) -> str:
        """
        Comment line if it contains Quarto include syntax.

        Include syntax is: `{{< include ... >}}`.

        Parameters
        ----------
        line : str
            The line to process.

        Returns
        -------
        str
            The input line, but commented if it had quarto include syntax.

        """
        if line.lstrip().startswith("{{< include ") and line.rstrip().endswith(
            ">}}"
        ):
            return f"# {line}"
        return line

    def handle_annotations(self, line: str) -> str:
        """
        Remove in-line quarto code annotations (and any whitespace prior).

        These include:
        - `#<<` used by shafayetShafee's line-highlight extension.
        - `# <n>` used by Quarto code annotations (e.g., `# <1>`).

        Parameters
        ----------
        line : str
            The line to process.

        Returns
        -------
        str
            The line with trailing whitespace and any "#<<" at the end removed.

        """
        # Strip "#<<" annotations
        line = re.sub(r"\s*#<<\s*$", "", line)
        # Strip Quarto code annotations like "# <1>"
        return re.sub(r"\s*# <\d+>\s*$", "", line)


class FormatOutputBuilder(OutputBuilder):
    """Build a formatter-friendly Python view."""

    def build(self, src_bytes: bytes) -> list[str]:
        """
        Populate `self.py_lines` for formatter, guided by block metadata.

        Each format-eligible block is emitted once, preceded by a durable
        separator comment. No placeholders or line-preservation logic are used.

        Parameters
        ----------
        src_bytes : bytes
            UTF-8 encoded document source.

        Returns
        -------
        py_lines: list[str]
            Lines for Python file.
        """
        all_lines = src_bytes.decode("utf-8", errors="replace").splitlines()

        for block in self.python_blocks:
            if not self.should_process_block(block):
                continue
            if block["is_valuebox"]:
                continue
            if block["first_code_row"] is None:
                continue

            block_index = block["block_index"]
            self.py_lines.append(f"{FORMAT_SEPARATOR_PREFIX}{block_index}")

            for row in range(block["first_code_row"], block["closing_row"]):
                if row in block["option_rows"]:
                    continue

                line = all_lines[row]

                if (
                    block["magic_row"] is not None
                    and row == block["magic_row"]
                ):
                    continue

                line = self.handle_includes(line)
                line = self.handle_annotations(line)
                self.py_lines.append(line)

            self.py_lines.append("")

        return self.py_lines


class LintOutputBuilder(OutputBuilder):
    """Build a lint-friendly Python view."""

    def __init__(
        self,
        *args: Any,  # noqa: ANN401
        max_line_length: int | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """
        Initialise LintOutputBuilder with OutputBuilder defaults + max line.

        Parameters
        ----------
        max_line_length : int or None
            Maximum allowed line length for lint suppression handling.
        """
        super().__init__(*args, **kwargs)
        self.max_line_length = max_line_length

    def build(self, src_bytes: bytes) -> list[str]:
        """
        Populate `self.py_lines` for linting, guided by block metadata.

        Parameters
        ----------
        src_bytes : bytes
            UTF-8 encoded document source.

        Returns
        -------
        py_lines: list[str]
            Lines for Python file.
        """
        # Decode document back into list of text lines so we can iterate by
        # row index (matching Tree-sitter's row numbering).
        all_lines = src_bytes.decode("utf-8", errors="replace").splitlines()
        total_rows = len(all_lines)

        # Build a fast lookup from row index -> block metadata, so for any
        # given line we can quickly tell whether it belongs to a Python chunk
        # and, if so, which one.
        row_to_block = self.make_row_to_block()

        # Walk through every row in the document and decide what to save
        # for that row in the output Python view.
        row = 0
        while row < total_rows:
            line = all_lines[row]
            block = row_to_block.get(row)

            # If this row is outside any Python block, save a placeholder
            # (to preserve line numbers) and move on.
            if block is None:
                self.append_placeholder()
                row += 1
                continue

            # We are inside a Python block: decide whether this chunk should
            # be processed at all, based on eval flags and YAML defaults.
            should_process = self.should_process_block(block)

            # Handle the opening/closing fence rows for the block.
            if self.handle_block_boundary_row(row, block):
                row += 1
                continue

            # If this row is part of the chunk-options region (e.g. `#|` lines,
            # leading comments), handle it separately from real code lines.
            stripped = line.lstrip()
            if row in block["option_rows"]:
                self.handle_option_row(
                    line, stripped, should_process=should_process
                )
                row += 1
                continue

            # Any remaining rows inside the block are treated as Python code
            # lines: possibly rewritten (includes/annotations/noqa) or masked
            # with placeholders depending on `should_process` and block flags.
            self.handle_code_row(
                row, line, stripped, block, should_process=should_process
            )
            row += 1

        return self.py_lines

    def make_row_to_block(self) -> dict[int, dict]:
        """
        Build a row-index to block mapping for fast lookups.

        Returns
        -------
        dict of int to dict
            A mapping from row index to the metadata dictionary for the
            block that covers that row.
        """
        row_to_block: dict[int, dict] = {}
        # For each Python block, mark every row it covers (from the opening
        # fence to the closing fence) as belonging to that block
        for block in self.python_blocks:
            for row in range(block["start_row"], block["closing_row"] + 1):
                row_to_block[row] = block
        return row_to_block

    def append_placeholder(self) -> None:
        """Append placeholder if preserving line count."""
        if self.preserve_line_count:
            self.py_lines.append("# -")

    def handle_block_boundary_row(self, row: int, block: dict) -> bool:
        """
        Handle opening/closing fence rows for a Python block.

        If line count preservation is enabled, these rows are replaced with
        placeholders so that the linter only sees Python code and comments.

        Parameters
        ----------
        row : int
            Current row index.
        block : dict
            Metadata for the enclosing Python block.

        Returns
        -------
        bool
            `True` if this row has been fully handled and the caller
            should skip further processing; `False` otherwise.
        """
        # Use a sentinel comment to mark the start of a chunk
        if row == block["start_row"]:
            if self.preserve_line_count:
                self.py_lines.append("# %% [python]")
            return True

        # Closing fence is represented by a placeholder
        if row == block["closing_row"]:
            if self.preserve_line_count:
                self.append_placeholder()
            return True

        return False

    def handle_option_row(
        self,
        line: str,
        stripped: str,
        *,
        should_process: bool,
    ) -> None:
        """
        Handle a row that belongs to the chunk-options region.

        Depending on the content and whether the block is linted, this
        either preserves the row as-is, replaces it with a placeholder, or
        strips Quarto-specific annotation syntax.

        Parameters
        ----------
        line : str
            Original line text.
        stripped : str
            Line text with leading whitespace removed.
        should_process : bool
            Whether the surrounding block is subject to linting.
        """
        # Preserve blank lines to keep vertical spacing stable
        if stripped == "":
            self.py_lines.append(line)
            return

        # Represent chunk option lines with a placeholder
        if stripped.startswith("#| "):
            self.append_placeholder()
            return

        # If should link (e.g., active chunk, or set to lint) then save line -
        # but otherwise (e.g., inactive chunk) just save placeholder
        if stripped.startswith("#"):
            if should_process:
                self.py_lines.append(self.handle_annotations(line))
            else:
                self.append_placeholder()
            return

        # Any other case is unexpected in the options region; use a
        # placeholder to avoid exposing non-code to the linter.
        self.append_placeholder()

    def handle_code_row(
        self,
        row: int,
        line: str,
        stripped: str,
        block: dict,
        *,
        should_process: bool,
    ) -> None:
        """
        Handle a non-boundary, non-option row inside a Python block.

        Parameters
        ----------
        row : int
            Zero-based row index.
        line : str
            Original line text.
        stripped : str
            Line text with leading whitespace removed.
        block : dict
            Metadata for the enclosing Python block.
        should_process : bool
            Whether this block is being linted.
        """
        # If the block should not be linted, or is a valuebox, mask all
        # code lines with placeholders.
        if not should_process or block["is_valuebox"]:
            self.append_placeholder()
            return

        # Convert Quarto include directives into comments and strip any
        # Quarto-specific trailing annotations.
        line = self.handle_includes(line)
        line = self.handle_annotations(line)

        magic_row = block.get("magic_row")
        first_code_row = block["first_code_row"]

        # Hide cell magic from the linter by replacing its line.
        if magic_row is not None and row == magic_row:
            self.append_placeholder()
            return

        # For linting tools that use `noqa`, add suppression rules to the first
        # code line in the chunk to avoid false positives.
        if row == first_code_row and row != magic_row and self.spacing_rules:
            line = self.add_noqa_for_first_code_line(line, stripped)

        self.py_lines.append(line)

    def add_noqa_for_first_code_line(self, line: str, stripped: str) -> str:
        """
        Add appropriate noqa suppressions for the first code line in a chunk.

        Always suppresses E305 (expected 2 blank lines after top-level
        statement). Also suppresses E302 if the line starts a function, class,
        or decorator.

        Parameters
        ----------
        line : str
            The line to add noqa comments to.
        stripped : str
            The line with leading whitespace removed.

        Returns
        -------
        str
            The line with appropriate noqa suppressions appended.

        """
        # Check for @ too as can have decorators - note, decorators are only
        # applied to functions or classes
        is_function_or_class = stripped.startswith(("@", "def", "class"))

        # Suppress E302 (expected 2 blank lines) in addition to E305
        if is_function_or_class:
            return self.add_noqa(line, ["E302", "E305"])
        return self.add_noqa(line, ["E305"])

    def add_noqa(self, line: str, suppress: list[str]) -> str:
        """
        Add noqa suppressions to a line for specified error codes.

        If the line is within the allowed max line length, E501 (line too long)
        is also suppressed, since the added noqa comment may push it over the
        limit.

        Parameters
        ----------
        line : str
            The line of code.
        suppress : list[str]
            The error code(s) to suppress (e.g. ["E302"]).

        Returns
        -------
        str
            The input line with 'noqa' suppressions appended as a comment.

        """
        if (
            self.max_line_length is not None
            and len(line) <= self.max_line_length
        ):
            suppress.append("E501")
        return f"{line.rstrip()}  # noqa: {','.join(suppress)}"
