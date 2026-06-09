"""Run tool on list of QMD files."""

import argparse
import sys
from collections.abc import Callable

from .processing import (
    format_qmd,
    process_qmd,
)


def _print_run_header(label: str) -> None:
    """
    Print a standard section header for a tool run.

    Parameters
    ----------
    label : str
        Name of tool being run.
    """
    print("==========================================================")
    print(f"Running {label}...")
    print("==========================================================")


def _run_across_files(
    qmd_files: list[str],
    label: str,
    runner: Callable[..., int],
    **runner_kwargs: object,
) -> int:
    """
    Run a processing function across all qmd files.

    Parameters
    ----------
    qmd_files : list[str]
        List of paths to `.qmd` files to process.
    label : str
        Human-readable label to print before running.
    runner : Callable[..., int]
        Function to call for each `.qmd` file.
    **runner_kwargs : object
        Extra keyword arguments forwarded to `runner`.

    Returns
    -------
    int
        Exit status. Returns 0 if all files are processed successfully,
        otherwise returns the highest non-zero exit code seen.
    """
    _print_run_header(label)
    exit_code = 0

    for qmd_file in qmd_files:
        try:
            ret = runner(qmd_file=qmd_file, **runner_kwargs)
        except Exception as e:  # noqa: BLE001
            print(
                f"Error: Unexpected error processing {qmd_file}: {e}",
                file=sys.stderr,
            )
            ret = 1

        exit_code = max(exit_code, ret)

    return exit_code


def run_formatter(
    qmd_files: list[str],
    formatter: str,
    args: argparse.Namespace,
) -> int:
    """
    Run one built-in formatter across all qmd files.

    Parameters
    ----------
    qmd_files : list[str]
        List of paths to `.qmd` files to process.
    formatter : str
        Tool to run against each generated temporary Python file.
    args : argparse.Namespace
        Parsed command-line arguments. Expected to provide `keep_temp`,
        `verbose`, and `lint_non_exec` attributes.
    """
    return _run_across_files(
        qmd_files=qmd_files,
        label=formatter,
        runner=format_qmd,
        formatter=formatter,
        keep_temp_files=args.keep_temp,
        verbose=args.verbose,
        lint_non_exec=args.lint_non_exec,
    )


def run_linter(
    qmd_files: list[str],
    linter: str,
    args: argparse.Namespace,
) -> int:
    """
    Run one built-in linter across all qmd files.

    Parameters
    ----------
    qmd_files : list[str]
        List of paths to `.qmd` files to process.
    linter : str
        Tool to run against each generated temporary Python file.
    args : argparse.Namespace
        Parsed command-line arguments. Expected to provide `keep_temp`,
        `verbose`, and `lint_non_exec` attributes.
    """
    return _run_across_files(
        qmd_files=qmd_files,
        label=linter,
        runner=process_qmd,
        linter=linter,
        keep_temp_files=args.keep_temp,
        verbose=args.verbose,
        lint_non_exec=args.lint_non_exec,
    )


def run_custom(
    qmd_files: list[str],
    command: list[str],
    args: argparse.Namespace,
) -> int:
    """
    Run one custom command across all qmd files.

    Parameters
    ----------
    qmd_files : list[str]
        List of paths to `.qmd` files to process.
    command : list[str]
        Custom command to run against each generated temporary Python file,
        represented as a list of command-line tokens.
    args : argparse.Namespace
        Parsed command-line arguments. Expected to provide `keep_temp`,
        `verbose`, and `lint_non_exec` attributes.
    """
    return _run_across_files(
        qmd_files=qmd_files,
        label=f"custom command: {' '.join(command)}",
        runner=process_qmd,
        custom_command=command,
        keep_temp_files=args.keep_temp,
        verbose=args.verbose,
        lint_non_exec=args.lint_non_exec,
    )
