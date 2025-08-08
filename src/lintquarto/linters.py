"""Retrieving linters."""

import shutil


class Linters:
    """
    Checks if requested linter (or static type checker) is available.

    Attributes
    ----------
    supported : dict
        Dictionary of supported linters - key is the name of the package, and
        value is the command that users would run before specifying files
        (e.g. "radon cc" - full command would then be "radon cc [file/dir]").
    """
    def __init__(self):
        """
        Initialise Linters instance.
        """
        self.supported = {
            # For pylint, disable missing-module-docstring (C0114) as this will
            # never be relevant for a quarto file.
            "pylint": ["pylint", "--disable=C0114"],
            "flake8": ["flake8"],
            "pyflakes": ["pyflakes"],
            "ruff": ["ruff", "check"],  # To specify linter (not formatter)
            "vulture": ["vulture"],
            "radon-cc": ["radon", "cc"],  # To compute cyclomatic complexity
            "radon-mi": ["radon", "mi"],  # To compute maintainability index
            "pycodestyle": ["pycodestyle"],
            "mypy": ["mypy"],
            "pyright": ["pyright"],
            "pyrefly": ["pyrefly", "check"],
            "pytype": ["pytype"]
        }

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
                f"{', '.join(self.supported.keys())}"
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
        if shutil.which(self.supported[linter_name][0]) is None:
            raise FileNotFoundError(
                f"{self.supported[linter_name][0]} not found. ",
                "Please install it."
            )
