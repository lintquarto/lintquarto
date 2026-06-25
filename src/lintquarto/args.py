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


class SingleMetavarHelpFormatter(argparse.HelpFormatter):
    """Show metavar only once for options with short and long forms."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        """
        Format the invocation string for a given action.

        Parameters
        ----------
        action : argparse.Action
            The action object describing the CLI option or positional
            argument to format.

        Returns
        -------
        str
            A human-readable invocation string. For optional arguments
            with both short and long option strings, the option flags
            are combined and the metavar is shown only once at the end.
            For positional arguments and flag-only options, the default
            formatting behaviour is preserved.
        """
        # Positional args: fall back to default behaviour
        if not action.option_strings:
            return super()._format_action_invocation(action)

        # Flags that take no value: just join option strings
        if action.nargs == 0:
            return ", ".join(action.option_strings)

        # Options that take a value: show all flags, then one args string
        default_metavar = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default_metavar)
        return f"{', '.join(action.option_strings)} {args_string}"


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
        formatter_class=SingleMetavarHelpFormatter,
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
        help="Quarto files and/or directories to run tools on.",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        nargs="*",
        default=[],
        metavar="[exclude_paths]",
        help="Files and/or directories to exclude from running tools on.",
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
