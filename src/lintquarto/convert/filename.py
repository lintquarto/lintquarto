"""Detect if filename already exists - if so, generate unique name."""

from pathlib import Path


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
