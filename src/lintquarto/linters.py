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

    def __init__(self) -> None:
        """Initialise Linters object."""
        self.supported = {
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
            # Specify linter and disable irrelevant checks
            "ruff": [
                "ruff",
                "check",
                "--config",
                "lint.ignore = ['RUF100', 'INP001']",
            ],
            "vulture": ["vulture"],
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
            msg = (
                f"Unsupported linter '{linter_name}'. Supported: "
                f"{', '.join(self.supported.keys())}",
            )
            raise ValueError(msg)

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
            msg = (
                f"{self.supported[linter_name][0]} not found. ",
                "Please install it.",
            )
            raise FileNotFoundError(msg)

    def status_list(self) -> list[dict[str, object]]:
        """
        Return list of availability of all supported linters.

        Returns
        -------
        list[dict[str, object]]
            List of dictionaries with linter name and availability.
        """
        status_list = []

        for name in self.supported:
            try:
                self.check_available(name)
                available = True
                message = "available"
            except FileNotFoundError:
                available = False
                message = "not found in PATH"
            except Exception as exc:  # noqa: BLE001
                available = False
                message = f"error checking availability: {exc}"

            status_list.append(
                {
                    "name": name,
                    "available": available,
                    "message": message,
                }
            )

        return status_list
