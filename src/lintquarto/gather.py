"""Function to gather a list of all QMD files."""

from pathlib import Path


def gather_qmd_files(
    paths: list[str | Path],
    exclude: list[str | Path] | None = None,
) -> list[str]:
    """
    Gather .qmd files from listed files/dirs, excluding specified paths.

    Parameters
    ----------
    paths : list[str | Path]
        List of file or directory paths.
    exclude : list[str | Path] | None
        List of files or directories to exclude. Defaults to None.

    Returns
    -------
    list[str]
        List of .qmd file paths found, excluding those in `exclude`.

    """
    exclude_paths = {Path(e).resolve() for e in (exclude or [])}
    files = []
    for path in paths:
        p = Path(path)
        # For files...
        if p.is_file() and p.suffix == ".qmd":
            abs_file = p.resolve()
            # Exclude if file or its parent dir is in exclude_paths
            if not any(
                abs_file == e or abs_file.is_relative_to(e)
                for e in exclude_paths
            ):
                files.append(str(abs_file))
        # For directories...
        elif p.is_dir():
            for f in p.rglob("*.qmd"):
                abs_file = f.resolve()
                if (
                    not any(
                        abs_file == e or abs_file.is_relative_to(e)
                        for e in exclude_paths
                    )
                    and abs_file.is_file()
                ):
                    files.append(str(abs_file))
    return files
