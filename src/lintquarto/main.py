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
    gather_qmd_files,
    validate_no_commas,
)
from .registry import Formatters, Linters
from .runner import ToolRunner

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

    # Run the formatters, linters and/or custom commands
    tool_runner = ToolRunner(
        qmd_files=qmd_files,
        keep_temp=args.keep_temp,
        verbose=args.verbose,
        lint_non_exec=args.lint_non_exec,
    )
    if args.formatters:
        for formatter in args.formatters:
            exit_code = max(exit_code, tool_runner.run_formatter(formatter))
    if args.linters:
        for linter in args.linters:
            exit_code = max(exit_code, tool_runner.run_linter(linter))
    if args.custom_commands:
        for command in custom_commands:
            exit_code = max(exit_code, tool_runner.run_custom(command))

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
