"""CustomArgumentParser."""

import argparse
import sys
from typing import Never


class CustomArgumentParser(argparse.ArgumentParser):
    """Print user-friendly error message and help text."""

    def error(self, message: str) -> Never:
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
