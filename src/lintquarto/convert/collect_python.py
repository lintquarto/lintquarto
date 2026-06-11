"""Identify and store Python code blocks from a QMD syntax tree."""

from tree_sitter import Node

from .analyse_python import analyse_block


def collect_python_blocks(src_bytes: bytes, root: Node) -> list[dict]:
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
    walk_for_python_blocks(src_bytes, root, blocks)

    # Sort by starting row so the blocks are in document order
    blocks.sort(key=lambda b: b["start_row"])

    # Add count to blocks (used by conversion for formatter)
    for i, block in enumerate(blocks):
        block["block_index"] = i

    return blocks


def walk_for_python_blocks(src_bytes: bytes, node: Node, blocks: list) -> None:
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
        lang_text = get_language_text(src_bytes, node)
        # Check for "python" (active) or ".python" (inactive)
        if lang_text is not None and lang_text.lstrip(".").lower() == "python":
            # Extract metadata from block and append to list
            blocks.append(analyse_block(src_bytes, node, lang_text))
        return

    # For each node, visit all of its children (then their children, etc.).
    # When a branch has no more children, the recursion returns and we
    # naturally move on to the next sibling. This way we eventually visit
    # every node in the tree.
    for child in node.children:
        walk_for_python_blocks(src_bytes, child, blocks)


def get_language_text(src_bytes: bytes, fcb_node: Node) -> str | None:
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
