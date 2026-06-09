"""Entry point for command line interface (CLI)."""

import argparse
import shlex
import shutil
import sys
from pathlib import Path

from .args import CustomArgumentParser, build_parser
from .config import load_config
from .merge import merge_config
from .processing import (
    format_qmd,
    gather_qmd_files,
    process_qmd,
    validate_no_commas,
)
from .registry import Formatters, Linters

# ============================================================================
# Main function: entry point for the lintquarto CLI.
# ============================================================================


def main() -> None:
    """
    Entry point for the lintquarto CLI.

    Parses arguments, processes .qmd files, and exits with appropriate status
    code.
    """
    parser = build_parser()
    args = parser.parse_args()

    # If list command, exit and run list_tools()
    if args.command == "list":
        return list_tools()

    # Load pyproject.toml config and back-fill any unset CLI args
    config = load_config()
    args = merge_config(args, config, verbose=args.verbose)

    linters = Linters()
    formatters = Formatters()
    validate_args(parser, args, linters, formatters)

    custom_commands = parse_custom_commands(args.custom_commands, linters)

    # Gather all .qmd files from the provided arguments
    qmd_files = gather_qmd_files(args.paths, exclude=args.exclude)
    if not qmd_files:
        print(f"No .qmd files found in {args.paths}.", file=sys.stderr)
        sys.exit(1)

    exit_code = 0

    if args.formatters:
        for formatter in args.formatters:
            exit_code = max(
                exit_code, run_formatter(qmd_files, formatter, args)
            )
    if args.linters:
        for linter in args.linters:
            exit_code = max(exit_code, run_linter(qmd_files, linter, args))
    if args.custom_commands:
        for command in custom_commands:
            exit_code = max(exit_code, run_custom(qmd_files, command, args))

    sys.exit(exit_code)


# ============================================================================
# Helpers which validate args and extract and validate custom commands
# ============================================================================


def validate_args(
    parser: CustomArgumentParser,
    args: argparse.Namespace,
    linters: Linters,
    formatters: Formatters,
) -> None:
    """
    Validate command-line arguments.

    Parameters
    ----------
    parser : CustomArgumentParser
        CLI argument parser.
    args : argparse.Namespace
        Parsed command-line arguments.
    linters : Linters
        Registry of supported linters.
    formatters : Formatters
        Registry of supported formatters.
    """
    if not args.paths:
        parser.error(
            "the following arguments are required for linting: -p/--paths "
            "(or set 'paths' under [tool.lintquarto] in pyproject.toml)"
        )
    if not args.linters and not args.formatters and not args.custom_commands:
        parser.error(
            "at least one tool is required: use -l/--linters, "
            "-f/--formatters, and/or --custom-commands (or set under "
            "[tool.lintquarto] in pyproject.toml)"
        )

    # Enforce space-separated paths with clear error
    validate_no_commas(args.paths, "paths")
    validate_no_commas(args.exclude, "exclude")

    # Fail fast on invalid or missing linters and formatters
    if args.linters:
        linters = Linters()
        try:
            for linter in args.linters:
                linters.check_supported(linter)
                linters.check_available(linter)
        except (ValueError, FileNotFoundError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    if args.formatters:
        formatters = Formatters()
        try:
            for formatter in args.formatters:
                formatters.check_supported(formatter)
                formatters.check_available(formatter)
        except (ValueError, FileNotFoundError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


def parse_custom_commands(
    raw_commands: list[str],
    linters: Linters,
) -> list[list[str]]:
    """
    Parse, validate, and warn on custom commands.

    Parameters
    ----------
    raw_commands : list[str]
        Raw custom command strings provided via repeated `--custom-commands`
        arguments.
    linters : Linters
        Supported linter registry, used to warn when a custom command
        executable matches a built-in supported linter.

    Returns
    -------
    custom_commands : list[list[str]]
        List of parsed custom commands, where each command is stored as a
        tokenised list of strings suitable for subprocess execution.
    """
    custom_commands = []
    try:
        for raw_command in raw_commands:
            parsed = shlex.split(raw_command, posix=(sys.platform != "win32"))
            if not parsed:
                print(
                    "Error: Custom command cannot be empty.", file=sys.stderr
                )
                sys.exit(1)

            executable = parsed[0]
            resolved = shutil.which(executable)
            if resolved is None and not Path(executable).exists():
                print(
                    (
                        "Error: Custom command executable not found: "
                        f"{executable}"
                    ),
                    file=sys.stderr,
                )
                sys.exit(1)

            for name, supported_command in linters.supported.items():
                supported_executable = supported_command[0]
                if executable == supported_executable:
                    print(
                        f"Warning: custom command '{executable}' matches "
                        f"supported linter '{name}'; prefer '-l {name}' with "
                        "configuration file.",
                        file=sys.stderr,
                    )
                    break

            custom_commands.append(parsed)

    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    return custom_commands


# ============================================================================
# List tools
# ============================================================================


def list_tools() -> None:
    """Print all supported tools and whether they're available."""
    print()  # Blank line
    for registry_cls, label in (
        (Linters, "linters"),
        (Formatters, "formatters"),
    ):
        registry = registry_cls()
        status_list = registry.status_list()
        print(
            f"Availability of supported {label} in your current environment:"
        )
        for status in status_list:
            flag = "✓" if status["available"] else "✗"
            print(f"  {flag} {status['name']:16s} - {status['message']}")
        print()  # Blank line


# ============================================================================
# Run formatter, linter or custom commands
# ============================================================================


def run_formatter(
    qmd_files: list[str], formatter: str, args: argparse.Namespace
) -> int:
    """
    Run one built-in formatter across all qmd files.

    Parameters
    ----------
    qmd_files : list[str]
        List of paths to `.qmd` files to process.
    formatter: str
        Tool to run against each generated temporary Python file.
    args : argparse.Namespace
        Parsed command-line arguments. Expected to provide `keep_temp`,
        `verbose`, and `lint_non_exec` attributes.

    Returns
    -------
    int
        Exit status for the custom command run. Returns 0 if all files are
        processed successfully, otherwise returns a non-zero code if any file
        fails.
    """
    print("==========================================================")
    print(f"Running {formatter}...")
    print("==========================================================")
    exit_code = 0
    for qmd_file in qmd_files:
        try:
            ret = format_qmd(
                qmd_file=qmd_file,
                formatter=formatter,
                keep_temp_files=args.keep_temp,
                verbose=args.verbose,
                lint_non_exec=args.lint_non_exec,
            )
        except Exception as e:  # noqa: BLE001
            print(
                f"Error: Unexpected error processing {qmd_file}: {e}",
                file=sys.stderr,
            )
            ret = 1
        if ret != 0:
            exit_code = ret
    return exit_code


def run_linter(
    qmd_files: list[str], linter: str, args: argparse.Namespace
) -> int:
    """
    Run one built-in linter across all qmd files.

    Parameters
    ----------
    qmd_files : list[str]
        List of paths to `.qmd` files to process.
    linter: str
        Tool to run against each generated temporary Python file.
    args : argparse.Namespace
        Parsed command-line arguments. Expected to provide `keep_temp`,
        `verbose`, and `lint_non_exec` attributes.

    Returns
    -------
    int
        Exit status for the custom command run. Returns 0 if all files are
        processed successfully, otherwise returns a non-zero code if any file
        fails.
    """
    print("==========================================================")
    print(f"Running {linter}...")
    print("==========================================================")
    exit_code = 0
    for qmd_file in qmd_files:
        try:
            ret = process_qmd(
                qmd_file=qmd_file,
                linter=linter,
                keep_temp_files=args.keep_temp,
                verbose=args.verbose,
                lint_non_exec=args.lint_non_exec,
            )
        except Exception as e:  # noqa: BLE001
            print(
                f"Error: Unexpected error processing {qmd_file}: {e}",
                file=sys.stderr,
            )
            ret = 1
        if ret != 0:
            exit_code = ret
    return exit_code


def run_custom(
    qmd_files: list[str], command: list[str], args: argparse.Namespace
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

    Returns
    -------
    int
        Exit status for the custom command run. Returns 0 if all files are
        processed successfully, otherwise returns a non-zero code if any file
        fails.
    """
    print("==========================================================")
    print(f"Running custom command: {' '.join(command)}...")
    print("==========================================================")
    exit_code = 0
    for qmd_file in qmd_files:
        try:
            ret = process_qmd(
                qmd_file=qmd_file,
                custom_command=command,
                keep_temp_files=args.keep_temp,
                verbose=args.verbose,
                lint_non_exec=args.lint_non_exec,
            )
        except Exception as e:  # noqa: BLE001
            print(
                f"Error: Unexpected error processing {qmd_file}: {e}",
                file=sys.stderr,
            )
            ret = 1
        if ret != 0:
            exit_code = ret
    return exit_code
