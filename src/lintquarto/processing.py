"""Core functions which gather and process quarto files."""

from __future__ import annotations

import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

from .converter import convert_qmd_to_py
from .registry import Linters


# Arguments after * are keyword-only (`var=True`, not just `True`)
@contextmanager
def temp_py_file(py_file: Path, *, keep: bool) -> Iterator[Path]:
    """Context manager that ensures file is removed on exit unless keep=True.

    Parameters
    ----------
    py_file : Path
        Path to the .py file.
    keep : bool
        Whether to keep the temporary .py file.
    """
    try:
        # Execution of the "with" block runs here, using py_file
        yield py_file
    # Everything after yield runs unconditionally when the with block exits
    # (whether normally, via return, or via an unhandled exception).
    finally:
        if not keep and py_file.exists():
            try:
                py_file.unlink()
            except Exception as e:  # noqa: BLE001
                print(
                    f"Warning: Could not remove temporary file {py_file}: {e}",
                    file=sys.stderr,
                )


def process_qmd(  # noqa: PLR0913
    qmd_file: str | Path,
    linter: str | None = None,
    custom_command: list[str] | None = None,
    *,  # Subsequent arguments are keyword-only (`var=True`, not just `True`)
    keep_temp_files: bool = False,
    verbose: bool = False,
    lint_non_exec: bool = False,
) -> int:
    """
    Convert a .qmd file to .py, lint it, and clean up.

    Parameters
    ----------
    qmd_file : str | Path
        Path to the input .qmd file.
    linter : str
        Name of the linter to use.
    custom_command : str
        Custom command to run against generated .py file.
    keep_temp_files : bool, optional
        If True, retain the temporary .py file after linting.
    verbose : bool, optional
        If True, print detailed progress information.
    lint_non_exec : bool, optional
        If True, also lint non-executable Python code chunks.

    Returns
    -------
    int
        0 on success, nonzero on error.

    """
    # Convert input to Path object
    qmd_path = Path(qmd_file)

    # Validate that the file exists and has a .qmd extension
    if not qmd_path.exists() or qmd_path.suffix != ".qmd":
        print(f"Error: {qmd_file} is not a valid .qmd file.", file=sys.stderr)
        return 1

    if (linter is None) == (custom_command is None):
        print(
            "Error: Provide exactly one of 'linter' or 'custom_command'.",
            file=sys.stderr,
        )
        return 1

    # Convert the .qmd file to a .py file
    try:
        py_file = convert_qmd_to_py(
            qmd_path=str(qmd_path),
            linter=linter,
            verbose=verbose,
            lint_non_exec=lint_non_exec,
        )
    # Catch for if the function raises an error
    except Exception as e:  # noqa: BLE001
        print(
            f"Error: Failed to convert {qmd_file} to .py: {e}",
            file=sys.stderr,
        )
        return 1

    # Catch for if the function returns None
    if py_file is None:
        print(
            f"Error: Failed to convert {qmd_file} to .py",
            file=sys.stderr,
        )
        return 1

    with temp_py_file(py_file=py_file, keep=keep_temp_files):
        try:
            if custom_command is not None:
                command = [*custom_command, str(py_file)]
            else:
                command = Linters().supported[linter] + [str(py_file)]

            # Run command on the temporary .py file and capture output
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            # Get the base filename from the full file paths
            qmd_filename = str(qmd_path.name)
            py_filename = str(py_file.name)

            # Replace all references to the .py file with the .qmd file
            result.stdout = result.stdout.replace(py_filename, qmd_filename)
            print(result.stdout, end="")

            # If there is an error - which will include some linter outputs
            # that get classed as errors - then also replace `.py` and print
            if result.stderr:
                result.stderr = result.stderr.replace(
                    py_filename, qmd_filename
                )
                print(result.stderr, file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(
                f"Error: Unexpected failure while linting {qmd_file}: {e}",
                file=sys.stderr,
            )
            return 1

    return 0


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


def validate_no_commas(list_of_paths: list[str], argname: str) -> None:
    """
    Check for commas in list of paths and raise ValueError if found.

    Parameters
    ----------
    list_of_paths : list[str]
        List of file or directory paths to check.
    argname : str
        Name of the argument for error messaging.

    Raises
    ------
    ValueError
        If any path contains a comma, indicating improper separation.

    """
    for path in list_of_paths:
        if "," in path:
            msg = (
                f"Argument '{argname}' contains a comma: '{path}'. Separate "
                "paths with spaces, not commas. e.g: -p file.qmd dir2"
            )
            raise ValueError(msg)
