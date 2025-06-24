"""Retrieving linters."""

import shutil


class Linters:
    """
    Checks if requested linter is available.

    Attributes
    ----------
    supported : list of str
        List of supported linters.
    """
    def __init__(self):
        """
        Initialise Linters instance.
        """
        self.supported = ["pylint", "flake8", "mypy"]

    def check_supported(self, linter_name):
        """
        Check if linter is supported by lintquarto.

        Parameters
        ----------
        linter_name : str
            Name of the linter to check.

        Raises
        ------
        ValueError
            If linter is not supported.
        """
        if linter_name not in self.supported:
            raise ValueError(
                f"Unsupported linter '{linter_name}'. Supported: " +
                f"{', '.join(self.supported)}"
            )

    def check_available(self, linter_name):
        """
        Check if a linter is available in the user's system.

        Parameters
        ----------
        linter_name : str
            Name of the linter to check.

        Raises
        ------
        FileNotFoundError
            If the linter's command is not found in the user's PATH.
        """
        # Check if the command (same as linter name) is available on the
        # user's system
        if shutil.which(linter_name) is None:
            raise FileNotFoundError(
                f"{linter_name} not found. Please install it."
            )
