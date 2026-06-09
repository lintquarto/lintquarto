"""Convert .qmd file to python file."""

from __future__ import annotations

import re
import warnings
from pathlib import Path
from typing import Literal

import tree_sitter_markdown as tsmd
import yaml
from tree_sitter import Language, Node, Parser

from .linelength import LineLengthDetector
from .registry import Formatters, Linters

SPACING_RULE_LINTERS = ["flake8", "ruff", "pycodestyle"]
NO_LINE_COUNT_PRESERVATION = ["radon-raw"]

FORMAT_SEPARATOR_PREFIX = "# %%LINTQUARTO-BLOCK-"


# ============================================================================
# Converter class
# ============================================================================


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
    py_lines : list[str]
        Stores the lines to be written to the output Python file.
    python_blocks : list[dict]
        List to store metadata for all Python blocks.
    yaml_eval_default : bool
        Default eval setting from YAML front matter.
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

        self.py_lines: list[str] = []
        self.python_blocks: list[dict] = []
        self.yaml_eval_default = True

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

    # -------------------------------------------------------------------------
    # Public method: used to convert QMD to Python.
    # -------------------------------------------------------------------------

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
        # Reset list to store Python lines
        self.py_lines = []

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
        metadata_node = self._find_metadata_node(root)
        if metadata_node is not None:
            # Use the YAML to configure the default `execute.eval` behaviour
            self.yaml_eval_default = self._parse_yaml_eval_from_node(
                src_bytes, metadata_node
            )
        else:
            # If there is no YAML front matter, fall back to eval=True
            self.yaml_eval_default = True

        # Find all fenced code blocks where the language is (active or
        # inactive) Python, and collect metadata about them
        self.python_blocks = self._collect_python_blocks(src_bytes, root)

        # Build the output Python view, line by line, guided by the block
        # metadata extracted above
        if self.mode == "lint":
            self._build_output(src_bytes)
        elif self.mode == "format":
            self._build_format_output(src_bytes)

        return self.py_lines

    # -------------------------------------------------------------------------
    # YAML front matter
    # -------------------------------------------------------------------------

    def _find_metadata_node(self, root: Node) -> Node | None:
        """
        Return the YAML front matter node, if present.

        Parameters
        ----------
        root : Node
            Root node of the parsed Markdown tree.

        Returns
        -------
        Node or None
            The first metadata node, or `None` if no metadata is present.
        """
        for child in root.children:
            # In Tree-sitter Markdown, YAML front matter is encoded as a
            # `minus_metadata` node
            if child.type == "minus_metadata":
                return child

        return None

    def _parse_yaml_eval_from_node(
        self, src_bytes: bytes, metadata_node: Node
    ) -> bool:
        """
        Parse YAML front matter and return execute.eval setting.

        This function takes the YAML metadata block at the top of the document,
        parses it, and looks for an `execute.eval` value. Various string forms
        (like "false", "no", "0") are normalised to a Python bool. If anything
        goes wrong, or no value is provided, it falls back to True.

        Parameters
        ----------
        src_bytes : bytes
            UTF-8 encoded document source.
        metadata_node : Node
            YAML metadata node (`minus_metadata`) from the AST.

        Returns
        -------
        bool
            The default eval setting; `True` if parsing fails or no explicit
            value is provided.
        """
        # Slice out just the YAML block from the original source bytes,
        # using the byte range of the metadata node, then decode to text lines
        raw = src_bytes[
            metadata_node.start_byte : metadata_node.end_byte
        ].decode("utf-8", errors="replace")
        lines = raw.splitlines()

        # YAML front matter sits between two '---' lines.
        # Skip the opening '---' on the first line, then collect lines
        # until the next '---' (the closing fence).
        yaml_lines = []
        for line in lines[1:]:
            if line.strip() == "---":
                break
            yaml_lines.append(line)

        # Try to parse the YAML text into a Python dict. If parsing fails
        # for any reason, fall back to the default behaviour: eval=True.
        try:
            yaml_dict = yaml.safe_load("\n".join(yaml_lines)) or {}
        except (yaml.YAMLError, AttributeError):
            return True

        # Look for an 'execute' section and then an 'eval' key inside it.
        # If it's a string, normalise common false-like values; otherwise
        # just coerce it to bool. If anything is missing, default to True.
        execute_settings = yaml_dict.get("execute", {})
        if isinstance(execute_settings, dict):
            eval_setting = execute_settings.get("eval", True)
            if isinstance(eval_setting, str):
                eval_setting = eval_setting.lower() not in [
                    "false",
                    "no",
                    "0",
                ]
            return bool(eval_setting)

        # If 'execute' is not a dict or not present, default to True
        return True

    # -------------------------------------------------------------------------
    # Find Python code chunks
    # -------------------------------------------------------------------------

    def _collect_python_blocks(
        self, src_bytes: bytes, root: Node
    ) -> list[dict]:
        """
        Collect all fenced Python code blocks in the document.

        Parameters
        ----------
        src_bytes : bytes
            UTF-8 encoded document source.
        root : Node
            Root node of the parsed Markdown tree.

        Returns
        -------
        list of dict
            A list of metadata dictionaries, one per Python code block.
        """
        # Empty list to store dicts - one dict for each Python code block
        blocks: list[dict] = []

        # Go through the syntax tree, adding nodes to the `blocks` list only
        # if they are fenced code blocks whose language is Python
        self._walk_for_python_blocks(src_bytes, root, blocks)

        # Sort by starting row so the blocks are in document order
        blocks.sort(key=lambda b: b["start_row"])

        # Add count to blocks (used by conversion for formatter)
        for i, block in enumerate(blocks):
            block["block_index"] = i

        return blocks

    def _walk_for_python_blocks(
        self, src_bytes: bytes, node: Node, blocks: list
    ) -> None:
        """
        Recursively search for fenced Python code blocks.

        Parameters
        ----------
        src_bytes : bytes
            UTF-8 encoded document source.
        node : Node
            Current node in the Tree-sitter AST.
        blocks : list
            Mutable list that is populated with block metadata dictionaries.
        """
        # Identify code blocks and get language
        if node.type == "fenced_code_block":
            lang_text = self._get_language_text(src_bytes, node)
            # Check for "python" (active) or ".python" (inactive)
            if (
                lang_text is not None
                and lang_text.lstrip(".").lower() == "python"
            ):
                # Extract metadata from block and append to list
                blocks.append(self._analyse_block(src_bytes, node, lang_text))
            return

        # For each node, visit all of its children (then their children, etc.).
        # When a branch has no more children, the recursion returns and we
        # naturally move on to the next sibling. This way we eventually visit
        # every node in the tree.
        for child in node.children:
            self._walk_for_python_blocks(src_bytes, child, blocks)

    def _get_language_text(
        self, src_bytes: bytes, fcb_node: Node
    ) -> str | None:
        """
        Extract the language tag from a fenced code block.

        Parameters
        ----------
        src_bytes : bytes
            UTF-8 encoded document source.
        fcb_node : Node
            A `fenced_code_block` node.

        Returns
        -------
        str or None
            The language text, or `None` if no language was specified.
        """
        for child in fcb_node.children:
            # Find the info_string node
            if child.type == "info_string":
                for grandchild in child.children:
                    # Find node whose type is language
                    if grandchild.type == "language":
                        # Get the string from the original file that
                        # corresponds to the bytes in that node
                        return src_bytes[
                            grandchild.start_byte : grandchild.end_byte
                        ].decode("utf-8", errors="replace")

        # Return None if no info_string with a language child was found
        return None

    # -------------------------------------------------------------------------
    # Inspect code chunks - e.g. identify active/inactive, valuebox, magic
    # -------------------------------------------------------------------------

    def _analyse_block(
        self, src_bytes: bytes, fcb_node: Node, lang_text: str
    ) -> dict:
        """
        Extract metadata for a single fenced Python code block.

        This combines structural information from the Tree-sitter node (start
        row, closing delimiter row) with line-level analysis from
        `_analyse_block_content`.

        Parameters
        ----------
        src_bytes : bytes
            UTF-8 encoded document source.
        fcb_node : Node
            A `fenced_code_block` node identified as Python.
        lang_text : str
            Raw language text for the block (e.g., `python` or `.python`).
        """
        # Top row of the fenced block (the opening ``` line)
        start_row = fcb_node.start_point.row
        # Row that contains the closing fence
        closing_row = self._find_closing_delimiter_row(fcb_node, start_row)
        # Node that contains the actual body of the code block
        content_node = self._find_content_node(fcb_node)

        # Analyse the content region to distinguish options and magic from
        # standard code lines
        content_info = self._analyse_block_content(
            src_bytes,
            content_node,
            closing_row,
        )

        return {
            "start_row": start_row,
            "closing_row": closing_row,
            "is_inactive": lang_text.startswith("."),
            "chunk_eval": content_info["chunk_eval"],
            "is_valuebox": content_info["is_valuebox"],
            "option_rows": content_info["option_rows"],
            "first_code_row": content_info["first_code_row"],
            "has_magic": content_info["has_magic"],
            "magic_row": content_info["magic_row"],
        }

    def _find_closing_delimiter_row(
        self, fcb_node: Node, start_row: int
    ) -> int:
        """
        Return the row number of the closing fenced-code delimiter (```).

        Parameters
        ----------
        fcb_node : Node
            A `fenced_code_block` node.
        start_row : int
            Row index of the opening fence.

        Returns
        -------
        int
            Row index of the closing fence line.
        """
        content_node = None

        # Find the content node if present
        for child in fcb_node.children:
            if child.type == "code_fence_content":
                content_node = child
                break

        # Use the content node if we have one. It's end_point.row is where the
        # content stops and the closing fence begins.
        if content_node is not None:
            closing_row = content_node.end_point.row
            if closing_row > start_row:
                return closing_row

        # Fallback: Look for fence delimiter nodes (``` lines) other than the
        # opening ones. This helps for blocks that have options or odd shapes
        # where the content node is missing or not reliable, but the fences
        # are still present as separate child nodes.
        delimiter_rows = [
            child.start_point.row
            for child in fcb_node.children
            if child.type == "fenced_code_block_delimiter"
            and child.start_point.row != start_row
        ]
        if delimiter_rows:
            return max(delimiter_rows)

        # Final fallback: use the overall node extent as a proxy.
        # end_point.row is typically one row beyond the closing fence, so
        # end_point.row - 1 is a reasonable estimate of the fence row.
        # This covers completely empty or malformed blocks where neither
        # content nor delimiter children are usable.
        return max(start_row + 1, fcb_node.end_point.row - 1)

    def _find_content_node(self, fcb_node: Node) -> Node | None:
        """
        Get the content of the code block.

        Parameters
        ----------
        fcb_node : Node
            A `fenced_code_block` node.

        Returns
        -------
        Node or None
            The content node inside the block, or `None` if there is no
            content (an empty fenced block).
        """
        for child in fcb_node.children:
            if child.type == "code_fence_content":
                return child
        return None

    def _analyse_block_content(
        self,
        src_bytes: bytes,
        content_node: Node | None,
        closing_row: int,
    ) -> dict:
        """
        Analyse the lines inside a fenced code block.

        This scans the content of a fenced Python block, identifying regions
        with chunk options and cell magic, and the actual code region.

        Parameters
        ----------
        src_bytes : bytes
            UTF-8 encoded document source.
        content_node : Node or None
            The `code_fence_content` node for the block, or `None` if
            the block has no content.
        closing_row : int
            Row index of the closing fence delimiter.

        Returns
        -------
        dict
            A dictionary with keys metadata such as the first code row, per-row
            option indices, and chunk-level flags.
        """
        # Set to store row indices of the options region
        option_rows: set[int] = set()

        state = {
            "first_code_row": None,
            "chunk_eval": None,
            "is_valuebox": False,
            "has_magic": False,
            "magic_row": None,
        }

        # We start in the 'options' region and remain there until we see the
        # first non-block, non-option, non-comment line.
        in_options = True

        if content_node is not None:
            content_start = content_node.start_point.row
            # The content region ends one row before the closing fence
            content_last = closing_row - 1
            for row_num, line in self._get_rows(
                src_bytes,
                content_start,
                content_last,
            ):
                stripped = line.lstrip()
                if in_options:
                    in_options = self._handle_option_state_row(
                        row_num,
                        stripped,
                        option_rows,
                        state,
                    )
                    continue

                # Once we exit the options region, every subsequent line for
                # this block is considered part of the code region
                self._mark_code_row(row_num, stripped, state)

        return {
            "option_rows": option_rows,
            "first_code_row": state["first_code_row"],
            "chunk_eval": state["chunk_eval"],
            "is_valuebox": state["is_valuebox"],
            "has_magic": state["has_magic"],
            "magic_row": state["magic_row"],
        }

    def _get_rows(
        self, src_bytes: bytes, start_row: int, end_row: int
    ) -> list[tuple[int, str]]:
        """
        Return (row_number, line_text) pairs for a given range of rows.

        Parameters
        ----------
        src_bytes : bytes
            UTF-8 encoded document source.
        start_row : int
            First row index to include.
        end_row : int
            Last row index to include (inclusive).

        Returns
        -------
        list of (int, str)
            A list of tuples containing the row index and corresponding
            line text for each row in the requested interval.
        """
        # Decode into str and split into lines
        # Row indices match Tree-sitter's `row` co-ordinates
        all_lines = src_bytes.decode("utf-8", errors="replace").splitlines()
        return [
            (row, all_lines[row])
            for row in range(start_row, min(end_row + 1, len(all_lines)))
        ]

    def _handle_option_state_row(
        self,
        row_num: int,
        stripped: str,
        option_rows: set[int],
        state: dict,
    ) -> bool:
        """
        Process a row while the parser is in the 'chunk options' region.

        This function classifies leading blank lines, Quarto chunk options
        (`#| ...`), and regular comments as option rows. It also updates
        per-block state such as `chunk_eval` and `is_valuebox`.

        Parameters
        ----------
        row_num : int
            Zero-based row index in the full document.
        stripped : str
            Line content with leading whitespace removed.
        option_rows : set of int
            Set being populated with row indices belonging to the options
            region of this block.
        state : dict
            Mutable analysis state for the current block.

        Returns
        -------
        bool
            `True` if the row was handled as an option row and the caller
            should remain in the options region; `False` if this row marks
            the transition into the code region.
        """
        # Empty lines at the top of the block are still considered part of
        # the options region
        if stripped == "":
            option_rows.add(row_num)
            return True

        # Lines starting with "#| " are explicit Quarto chunk options
        if stripped.startswith("#| "):
            option_rows.add(row_num)
            option_text = stripped[3:].strip()

            # Update the eval behaviour for this chunk, if an eval option
            # appears on this line
            state["chunk_eval"] = self._parse_chunk_eval(
                option_text,
                current_eval=state["chunk_eval"],
            )

            # Detect "content: valuebox" so we can treat valuebox chunks as
            # non-lintable later.
            if re.match(r"^content\s*:\s*valuebox\s*$", option_text):
                state["is_valuebox"] = True
            return True

        # Any other comment-only line at the top is also treated as part of
        # the options region.
        if stripped.startswith("#"):
            option_rows.add(row_num)
            return True

        # If we reach here, this line is not part of the options region.
        # Mark it as code and signal that the options region has ended.
        self._mark_code_row(row_num, stripped, state)
        return False

    def _parse_chunk_eval(
        self, option_text: str, *, current_eval: bool | None
    ) -> bool | None:
        """
        Parse an ``eval:`` option from a chunk option line.

        Parameters
        ----------
        option_text : str
            Text of the chunk option line (e.g., `eval: true`).
        current_eval : bool or None
            Existing eval value for the chunk. If no `eval` option is
            found, this value is returned unchanged.

        Returns
        -------
        bool or None
            Updated eval flag for this chunk, or `None` if the option
            cannot be interpreted.
        """
        # Search for an 'eval: value' pattern with optional quotes
        eval_match = re.search(r"eval\s*:\s*(['\"]?)(\w+)\1", option_text)
        if not eval_match:
            return current_eval

        value = eval_match.group(2).lower()
        if value in ["true", "yes", "1"]:
            return True
        if value in ["false", "no", "0"]:
            return False
        return None

    def _mark_code_row(
        self,
        row_num: int,
        stripped: str,
        state: dict,
    ) -> None:
        """
        Record first code row and magic metadata.

        Parameters
        ----------
        row_num : int
            Zero-based row index in the full document.
        stripped : str
            The line content with leading whitespace removed.
        state : dict
            Mutable analysis state for the current block.
        """
        # The first line that is not considered part of the options region
        # is the first code row.
        if state["first_code_row"] is None:
            state["first_code_row"] = row_num

        # Treat any line starting with '%%' as cell magic, and record where
        # it appears so it can be handled specially later.
        if stripped.startswith("%%"):
            state["has_magic"] = True
            state["magic_row"] = row_num

    # -------------------------------------------------------------------------
    # Construct Python file for linting, guided by metadata collected above
    # -------------------------------------------------------------------------

    def _build_output(self, src_bytes: bytes) -> None:
        """
        Populate `self.py_lines` from the source, guided by block metadata.

        This walks the document line by line, consults the per-row block
        mapping, and delegates handling of each row to the appropriate
        helper (boundary, option, or code). Non-Python lines are replaced
        with placeholders when line-count preservation is enabled.

        Parameters
        ----------
        src_bytes : bytes
            UTF-8 encoded document source.
        """
        # Decode document back into list of text lines so we can iterate by
        # row index (matching Tree-sitter's row numbering).
        all_lines = src_bytes.decode("utf-8", errors="replace").splitlines()
        total_rows = len(all_lines)

        # Build a fast lookup from row index -> block metadata, so for any
        # given line we can quickly tell whether it belongs to a Python chunk
        # and, if so, which one.
        row_to_block = self._make_row_to_block()

        # Walk through every row in the document and decide what to save
        # for that row in the output Python view.
        row = 0
        while row < total_rows:
            line = all_lines[row]
            block = row_to_block.get(row)

            # If this row is outside any Python block, save a placeholder
            # (to preserve line numbers) and move on.
            if block is None:
                self._append_placeholder()
                row += 1
                continue

            # We are inside a Python block: decide whether this chunk should
            # be processed at all, based on eval flags and YAML defaults.
            should_process = self.should_process_block(block)

            # Handle the opening/closing fence rows for the block.
            if self._handle_block_boundary_row(row, block):
                row += 1
                continue

            # If this row is part of the chunk-options region (e.g. `#|` lines,
            # leading comments), handle it separately from real code lines.
            stripped = line.lstrip()
            if row in block["option_rows"]:
                self._handle_option_row(
                    line, stripped, should_process=should_process
                )
                row += 1
                continue

            # Any remaining rows inside the block are treated as Python code
            # lines: possibly rewritten (includes/annotations/noqa) or masked
            # with placeholders depending on `should_process` and block flags.
            self._handle_code_row(
                row, line, stripped, block, should_process=should_process
            )
            row += 1

    def _make_row_to_block(self) -> dict[int, dict]:
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

    def _append_placeholder(self) -> None:
        """Append placeholder if preserving line count."""
        if self.preserve_line_count:
            self.py_lines.append("# -")

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

    def _handle_block_boundary_row(self, row: int, block: dict) -> bool:
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
                self._append_placeholder()
            return True

        return False

    def _handle_option_row(
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
            self._append_placeholder()
            return

        # If should link (e.g., active chunk, or set to lint) then save line -
        # but otherwise (e.g., inactive chunk) just save placeholder
        if stripped.startswith("#"):
            if should_process:
                self.py_lines.append(self._handle_annotations(line))
            else:
                self._append_placeholder()
            return

        # Any other case is unexpected in the options region; use a
        # placeholder to avoid exposing non-code to the linter.
        self._append_placeholder()

    def _handle_code_row(
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
            self._append_placeholder()
            return

        # Convert Quarto include directives into comments and strip any
        # Quarto-specific trailing annotations.
        line = self._handle_includes(line)
        line = self._handle_annotations(line)

        magic_row = block.get("magic_row")
        first_code_row = block["first_code_row"]

        # Hide cell magic from the linter by replacing its line.
        if magic_row is not None and row == magic_row:
            self._append_placeholder()
            return

        # For linting tools that use `noqa`, add suppression rules to the first
        # code line in the chunk to avoid false positives.
        if row == first_code_row and row != magic_row and self.spacing_rules:
            line = self._add_noqa_for_first_code_line(line, stripped)

        self.py_lines.append(line)

    def _add_noqa_for_first_code_line(self, line: str, stripped: str) -> str:
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
            return self._add_noqa(line, ["E302", "E305"])
        return self._add_noqa(line, ["E305"])

    def _add_noqa(self, line: str, suppress: list[str]) -> str:
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
        if len(line) <= self.max_line_length:
            suppress.append("E501")
        return f"{line.rstrip()}  # noqa: {','.join(suppress)}"

    def _handle_includes(self, line: str) -> str:
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

    def _handle_annotations(self, line: str) -> str:
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

    # -------------------------------------------------------------------------
    # Construct Python file for formatter, guided by metadata collected above
    # -------------------------------------------------------------------------

    def _build_format_output(self, src_bytes: bytes) -> None:
        """
        Build a formatter-friendly Python file.

        Each format-eligible block is emitted once, preceded by a durable
        separator comment. No placeholders or line-preservation logic are used.

        Parameters
        ----------
        src_bytes : bytes
            UTF-8 encoded document source.
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

                line = self._handle_includes(line)
                line = self._handle_annotations(line)
                self.py_lines.append(line)

            self.py_lines.append("")


def get_unique_filename(path: str | Path) -> Path:
    """
    Generate unique path by adding "_n" before the file extension, if needed.

    If the given path already exists, this function appends an incrementing
    number before the file extension (e.g., "file_1.py") until an unused
    filename is found.

    Parameters
    ----------
    path : str | Path
        The initial file path to check.

    Returns
    -------
    Path
        A unique file path that does not currently exist.
    """
    path = Path(path)
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    n = 1
    while True:
        new_path = parent / f"{stem}_{n}{suffix}"
        if not new_path.exists():
            return new_path
        n += 1


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
        print(f"Error during conversion: {e}")
        return None

    if formatter is not None:
        return output_path, converter
    return output_path


def recreate_qmd_from_formatted_py(
    qmd_path: str | Path,
    py_path: str | Path,
    python_blocks: list[dict],
    *,
    verbose: bool = False,
) -> Path:
    """
    Recreate a QMD file by splicing formatted Python back into its blocks.

    Parameters
    ----------
    qmd_path : str | Path
        Path to the original `.qmd` file.
    py_path : str | Path
        Path to the formatted temporary `.py` file.
    python_blocks : list[dict]
        Block metadata collected by `QmdToPyConverter`.
    verbose : bool, optional
        If True, print progress information.

    Returns
    -------
    Path
        Path to the rewritten `.qmd` file.
    """
    qmd_path = Path(qmd_path)
    py_path = Path(py_path)

    with qmd_path.open(encoding="utf-8") as f:
        qmd_lines = f.readlines()

    with py_path.open(encoding="utf-8") as f:
        py_lines = f.read().splitlines()

    formatted_blocks = _parse_formatted_blocks(py_lines)

    for block in sorted(
        python_blocks, key=lambda b: b["block_index"], reverse=True
    ):
        block_index = block["block_index"]

        if block_index not in formatted_blocks:
            continue
        if block["first_code_row"] is None:
            continue

        start = block["first_code_row"]
        end = block["closing_row"]

        qmd_lines[start:end] = [
            line + "\n" for line in formatted_blocks[block_index]
        ]

    with qmd_path.open("w", encoding="utf-8") as f:
        f.writelines(qmd_lines)

    if verbose:
        print(f"✓ Recreated {qmd_path} from formatted Python")

    return qmd_path


def _parse_formatted_blocks(py_lines: list[str]) -> dict[int, list[str]]:
    """
    Parse formatter output into per-block Python snippets.

    The formatted Python file consists of one or more blocks separated by
    marker lines of the form `f"{FORMAT_SEPARATOR_PREFIX}{index}"`,
    where `index` is an integer block index. Each separator starts a new
    block; all following lines up to the next separator (or end of file)
    belong to that block. Trailing blank lines within each block are
    stripped.

    Parameters
    ----------
    py_lines : list[str]
        Lines read from the temporary formatted Python file.

    Returns
    -------
    blocks : dict[int, list[str]]
        Mapping from block index to the list of formatted Python source
        lines for that block (without trailing blank lines).
    """
    blocks: dict[int, list[str]] = {}
    current_index: int | None = None
    current_lines: list[str] = []

    for line in py_lines:
        if line.startswith(FORMAT_SEPARATOR_PREFIX):
            if current_index is not None:
                while current_lines and current_lines[-1] == "":
                    current_lines.pop()
                blocks[current_index] = current_lines

            suffix = line.removeprefix(FORMAT_SEPARATOR_PREFIX).strip()
            current_index = int(suffix)
            current_lines = []
            continue

        if current_index is not None:
            current_lines.append(line)

    if current_index is not None:
        while current_lines and current_lines[-1] == "":
            current_lines.pop()
        blocks[current_index] = current_lines

    return blocks


if __name__ == "__main__":
    pass
