"""Retrieving linters."""

import shutil


class Linters:
    """
    Checks if requested linter (or static type checker) is available.

    Attributes
    ----------
    supported : dict
        Dictionary of supported linters. The key (e.g. `radon-cc`) maps to the
        full command (e.g. `["radon", "cc"]`).
    """
    supported: dict = {
        "flake8": ["flake8"],
        "mypy": ["mypy"],
        "pycodestyle": ["pycodestyle"],
        "pydoclint": ["pydoclint"],
        "pyflakes": ["pyflakes"],
        # Disable missing module docstring (C0114) as not relevant for qmd
        "pylint": ["pylint", "--disable=C0114"],
        "pyright": ["pyright"],
        "pyrefly": ["pyrefly", "check"],
        "pytype": ["pytype"],
        "radon-cc": ["radon", "cc"],  # To compute cyclomatic complexity
        "radon-mi": ["radon", "mi"],  # To compute maintainability index
        "radon-raw": ["radon", "raw"],  # To compute raw metrics
        "radon-hal": ["radon", "hal"],  # To compute halstead metrics
        "ruff": ["ruff", "check"],  # To specify linter (not formatter)
        "vulture": ["vulture"]
    }

    def check_supported(self, linter_name: str) -> None:
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
                f"Unsupported linter '{linter_name}'. Supported: "
                f"{', '.join(self.supported.keys())}"
            )

    def check_available(self, linter_name: str) -> None:
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
