"""Parse CLI arguments."""

import argparse
import sys
from typing import NoReturn

from lintquarto.registry import Formatters, Linters


class CustomArgumentParser(argparse.ArgumentParser):
    """Print user-friendly error message and help text."""

    def error(self, message: str) -> NoReturn:
        """
        Print error message.

        Parameters
        ----------
        message : str
            The error message to display.

        """
        print(f"\n❌ Error: {message}\n", file=sys.stderr)
        self.print_help()
        sys.exit(2)


def build_parser() -> CustomArgumentParser:
    """
    Create and configure the CLI argument parser.

    Returns
    -------
    parser : CustomArgumentParser
        CLI argument parser.
    """
    linters = list(Linters().supported.keys())
    formatters = list(Formatters().supported.keys())

    # Set up custom argumentparser with help statements
    parser = CustomArgumentParser(
        description="Lint Python code in Quarto (.qmd) files.",
        epilog=(
            "Configuration can also be provided in pyproject.toml under "
            "[tool.lintquarto]. CLI arguments override configuration file."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Subcommands
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=False,
    )
    subparsers.add_parser(
        "list",
        help="List supported linters and whether they are available.",
    )

    # Default commands
    parser.add_argument(
        "-l",
        "--linters",
        nargs="+",
        required=False,
        choices=linters,
        metavar="LINTER",
        help=f"Linters to run. Valid options: {linters}",
    )
    parser.add_argument(
        "-f",
        "--formatters",
        nargs="+",
        required=False,
        choices=formatters,
        metavar="FORMATTER",
        help=f"Formatter to run. Valid options: {formatters}.",
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
