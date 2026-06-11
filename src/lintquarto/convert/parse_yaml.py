"""Parse YAML front matter from a QMD document tree."""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from tree_sitter import Node


def find_metadata_node(root: Node) -> Node | None:
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


def parse_yaml_eval_from_node(src_bytes: bytes, metadata_node: Node) -> bool:
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
    raw = src_bytes[metadata_node.start_byte : metadata_node.end_byte].decode(
        "utf-8", errors="replace"
    )
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
