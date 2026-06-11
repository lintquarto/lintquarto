"""CustomArgumentParser."""

import argparse
import sys
from typing import NoReturn


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
