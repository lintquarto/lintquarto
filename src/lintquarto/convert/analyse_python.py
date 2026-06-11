"""Analyse Python code chunks and extract line-level metadata.

The metadata is used for linting and execution control. It determines whether a
block is active or inactive, identifies Quarto chunk options, detects valuebox
chunks, tracks cell magics, and records the first line of executable code in a
block.
"""

import re

from tree_sitter import Node


def analyse_block(src_bytes: bytes, fcb_node: Node, lang_text: str) -> dict:
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
    closing_row = find_closing_delimiter_row(fcb_node, start_row)
    # Node that contains the actual body of the code block
    content_node = find_content_node(fcb_node)

    # Analyse the content region to distinguish options and magic from
    # standard code lines
    content_info = analyse_block_content(
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


def find_closing_delimiter_row(fcb_node: Node, start_row: int) -> int:
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


def find_content_node(fcb_node: Node) -> Node | None:
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


def analyse_block_content(
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
        for row_num, line in get_rows(
            src_bytes,
            content_start,
            content_last,
        ):
            stripped = line.lstrip()
            if in_options:
                in_options = handle_option_state_row(
                    row_num,
                    stripped,
                    option_rows,
                    state,
                )
                continue

            # Once we exit the options region, every subsequent line for
            # this block is considered part of the code region
            mark_code_row(row_num, stripped, state)

    return {
        "option_rows": option_rows,
        "first_code_row": state["first_code_row"],
        "chunk_eval": state["chunk_eval"],
        "is_valuebox": state["is_valuebox"],
        "has_magic": state["has_magic"],
        "magic_row": state["magic_row"],
    }


def get_rows(
    src_bytes: bytes, start_row: int, end_row: int
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


def handle_option_state_row(
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
        state["chunk_eval"] = parse_chunk_eval(
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
    mark_code_row(row_num, stripped, state)
    return False


def parse_chunk_eval(
    option_text: str, *, current_eval: bool | None
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


def mark_code_row(
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
