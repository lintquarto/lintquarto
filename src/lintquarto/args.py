"""CustomArgumentParser."""

import argparse
import sys


class CustomArgumentParser(argparse.ArgumentParser):
    """Print user-friendly error message and help text."""

    def error(self, message: str) -> None:
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
