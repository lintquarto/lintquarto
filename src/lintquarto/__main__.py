"""Command-line interface (CLI) for running the package + main functions."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .args import CustomArgumentParser
from .converter import convert_qmd_to_py
from .linters import Linters


def process_qmd(
    qmd_file: str | Path,
    linter: str,
    *,  # Subsequent arguments are keyword-only (`var=True`, not just `True`)
    keep_temp_files: bool = False,
    verbose: bool = False,
) -> int:
    """
    Convert a .qmd file to .py, lint it, and clean up.

    Parameters
    ----------
    qmd_file : str | Path
        Path to the input .qmd file.
    linter : str
        Name of the linter to use (pylint, flake8, mypy).
    keep_temp_files : bool, optional
        If True, retain the temporary .py file after linting.
    verbose : bool, optional
        If True, print detailed progress information.

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

    # Check if linter is supported by lintquarto and available on user's system
    # Uses return codes 0 & 1 for CLI/shell compatability, as will be run
    # from the command line
    linters = Linters()
    try:
        linters.check_supported(linter)
        linters.check_available(linter)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Convert the .qmd file to a .py file
    try:
        py_file = convert_qmd_to_py(
            qmd_path=str(qmd_path), linter=linter, verbose=verbose)
        if py_file is None:
            print(f"Error: Failed to convert {qmd_file} to .py",
                  file=sys.stderr)
            return 1
    # Intentional broad catch for unknown conversion errors
    except Exception as e:  # noqa: BLE001
        print(f"Error: Failed to convert {qmd_file} to .py: {e}",
              file=sys.stderr)
        return 1

    # Run linter on the temporary .py file and capture output
    command = linters.supported[linter] + [str(py_file)]
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

    # If there is an error - which will include some linter outputs that get
    # classed as errors - then also replace `.py` and then print
    if result.stderr:
        result.stderr = result.stderr.replace(py_filename, qmd_filename)
        print(result.stderr, file=sys.stderr)

    # Remove temporary .py file unless keep_temp_files is set
    if not keep_temp_files:
        try:
            py_file.unlink()
        # Broad catch ensures cleanup warnings don't crash process
        except Exception as e:  # noqa: BLE001
            print(f"Warning: Could not remove temporary file {py_file}: {e}",
                  file=sys.stderr)
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
            if not any(abs_file == e or abs_file.is_relative_to(e)
                       for e in exclude_paths):
                files.append(str(abs_file))
        # For directories...
        elif p.is_dir():
            for f in p.rglob("*.qmd"):
                abs_file = f.resolve()
                if not any(abs_file == e or abs_file.is_relative_to(e)
                           for e in exclude_paths):
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


def main() -> None:
    """
    Entry point for the lintquarto CLI.

    Parses arguments, processes .qmd files, and exits with appropriate status
    code.
    """
    # Set up custom argumentparser with help statements
    parser = CustomArgumentParser(
        description="Lint Python code in Quarto (.qmd) files.",
    )
    parser.add_argument(
        "-l", "--linters", nargs="+", required=True,
        choices=list(Linters().supported.keys()), metavar="LINTER",
        help=("Linters to run. Valid options: "
              f"{list(Linters().supported.keys())}"),
    )
    parser.add_argument(
        "-p", "--paths", nargs="+", required=True,
        help="Quarto files and/or directories to lint.",
    )
    parser.add_argument(
        "-e", "--exclude", nargs="*", default=[], metavar="[exclude_paths]",
        help=("Files and/or directories to exclude from linting."),
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Verbose output.",
    )
    parser.add_argument(
        "-k", "--keep-temp", action="store_true",
        help="Keep temporary .py files after linting.",
    )
    args = parser.parse_args()

    # Enforce space-separated paths with clear error
    validate_no_commas(args.paths, "paths")
    validate_no_commas(args.exclude, "exclude")

    # Gather all .qmd files from the provided arguments
    qmd_files = gather_qmd_files(args.paths, exclude=args.exclude)
    if not qmd_files:
        print(f"No .qmd files found in {args.paths}.", file=sys.stderr)
        sys.exit(1)

    exit_code = 0
    # Process each .qmd file found using each linter
    for linter in args.linters:
        print("=============================================================")
        print(f"Running {linter}...")
        print("=============================================================")
        for qmd_file in qmd_files:
            ret = process_qmd(qmd_file=qmd_file,
                              linter=linter,
                              keep_temp_files=args.keep_temp,
                              verbose=args.verbose)
            if ret != 0:
                exit_code = ret
    sys.exit(exit_code)


if __name__ == "__main__":
    # Run the main function if this module is executed as a script
    main()
