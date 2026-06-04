"""Entry point for command line interface (CLI)."""

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
        choices=list(Linters().supported.keys()),
        metavar="LINTER",
        help=(
            "Linters to run. Valid options: "
            f"{list(Linters().supported.keys())}"
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
        help=("Files and/or directories to exclude from linting."),
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

    args = parser.parse_args()

    # If list command, exit and run list_linters()
    if args.command == "list":
        return list_linters()

    # Enforce that we have arguments required for lint mode
    if not args.linters or not args.paths:
        parser.error(
            "the following arguments are required for linting: "
            "-l/--linters, -p/--paths"
        )

    # Enforce space-separated paths with clear error
    validate_no_commas(args.paths, "paths")
    validate_no_commas(args.exclude, "exclude")

    # Fail fast on invalid or missing linters
    linters = Linters()
    try:
        for linter in args.linters:
            linters.check_supported(linter)
            linters.check_available(linter)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

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
    sys.exit(exit_code)


def list_linters() -> None:
    """Print all supported linters and whether they're available."""
    linters = Linters()
    status_list = linters.status_list()
    print("Availability of supported linters:")
    for status in status_list:
        flag = "✓" if status["available"] else "✗"
        print(f"  {flag} {status['name']:12s} - {status['message']}")
