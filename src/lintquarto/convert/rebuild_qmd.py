"""Rebuild a QMD file."""

from pathlib import Path

from .constants import FORMAT_SEPARATOR_PREFIX


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

    formatted_blocks = parse_formatted_blocks(py_lines)

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


def parse_formatted_blocks(py_lines: list[str]) -> dict[int, list[str]]:
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
