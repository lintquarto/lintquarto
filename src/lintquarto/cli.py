"""Entry point for command line interface (CLI)."""

import argparse
import shlex
import shutil
import sys

from .args import CustomArgumentParser
from .linters import Linters
from .processing import gather_qmd_files, process_qmd, validate_no_commas


def main() -> None:
    """
    Entry point for the lintquarto CLI.

    Parses arguments, processes .qmd files, and exits with appropriate status
    code.
    """
    parser = build_parser()
    args = parser.parse_args()

    # If list command, exit and run list_linters()
    if args.command == "list":
        return list_linters()

    linters = Linters()
    validate_args(parser, args, linters)

    custom_commands = parse_custom_commands(args.custom_commands, linters)

    # Gather all .qmd files from the provided arguments
    qmd_files = gather_qmd_files(args.paths, exclude=args.exclude)
    if not qmd_files:
        print(f"No .qmd files found in {args.paths}.", file=sys.stderr)
        sys.exit(1)

    exit_code = 0

    if args.linters:
        for linter in args.linters:
            exit_code = max(exit_code, run_linter(qmd_files, linter, args))
    if args.custom_commands:
        for command in custom_commands:
            exit_code = max(exit_code, run_custom(qmd_files, command, args))

    sys.exit(exit_code)


def build_parser() -> CustomArgumentParser:
    """
    Create and configure the CLI argument parser.

    Returns
    -------
    parser : CustomArgumentParser
        CLI argument parser.
    """
    linters = Linters()

    # Set up custom argumentparser with help statements
    parser = CustomArgumentParser(
        description="Lint Python code in Quarto (.qmd) files.",
    )

    # Subcommands: list available linters in environment
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=False,
    )
    subparsers.add_parser(
        "list",
        help="List supported linters and whether they are available.",
    )

    # Default: Running tools
    parser.add_argument(
        "-l",
        "--linters",
        nargs="+",
        required=False,
        choices=list(linters.supported.keys()),
        metavar="LINTER",
        help=(
            f"Linters to run. Valid options: {list(linters.supported.keys())}"
        ),
    )
    parser.add_argument(
        "-p",
        "--paths",
        nargs="+",
        required=False,
        help="Quarto files and/or directories to lint.",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        nargs="*",
        default=[],
        metavar="[exclude_paths]",
        help="Files and/or directories to exclude from linting.",
    )
    parser.add_argument(
        "-n",
        "--lint-non-exec",
        action="store_true",
        help="Also lint non-executable Python code chunks",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output.",
    )
    parser.add_argument(
        "-k",
        "--keep-temp",
        action="store_true",
        help="Keep temporary .py files after linting.",
    )
    parser.add_argument(
        "-c",
        "--custom-commands",
        action="append",
        default=[],
        metavar="COMMAND",
        help=(
            "Custom command to run against the generated .py file. "
            "Repeat for multiple commands. "
            'Example: --custom-commands "mytool"'
        ),
    )

    return parser


def validate_args(
    parser: CustomArgumentParser, args: argparse.Namespace, linters: Linters
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
        Registry of supported linters, used to validate requested linters.
    """
    # Enforce that we have arguments required for lint mode
    if not args.paths:
        parser.error(
            "the following arguments are required for linting: -p/--paths"
        )
    if not args.linters and not args.custom_commands:
        parser.error(
            "at least one linter is required: use -l/--linters and/or "
            "--custom-commands"
        )

    # Enforce space-separated paths with clear error
    validate_no_commas(args.paths, "paths")
    validate_no_commas(args.exclude, "exclude")

    # Fail fast on invalid or missing linters
    linters = Linters()
    if args.linters:
        try:
            for linter in args.linters:
                linters.check_supported(linter)
                linters.check_available(linter)
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
            parsed = shlex.split(raw_command)
            if not parsed:
                print(
                    "Error: Custom command cannot be empty.", file=sys.stderr
                )
                sys.exit(1)

            executable = parsed[0]
            resolved = shutil.which(executable)
            if resolved is None:
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


def list_linters() -> None:
    """Print all supported linters and whether they're available."""
    linters = Linters()
    status_list = linters.status_list()
    print("Availability of supported linters:")
    for status in status_list:
        flag = "✓" if status["available"] else "✗"
        print(f"  {flag} {status['name']:12s} - {status['message']}")


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
