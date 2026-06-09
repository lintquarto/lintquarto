"""Retrieve supported linters."""

import shutil


class ToolRegistry:
    """
    Registry of supported external tools.

    Attributes
    ----------
    supported : dict[str, list[str]]
        Dictionary of supported tools. The key (e.g. `radon-cc`) maps to the
        full command (e.g. `["radon", "cc"]`).
    tool_label : str
        Used in error messages, e.g., "linter" or "formatter".

    """

    def __init__(self, supported: dict[str, list[str]]) -> None:
        """
        Initialise Linters object.

        Parameters
        ----------
        supported : dict[str, list[str]]
            Dictionary of supported tools. The key (e.g. `radon-cc`) maps to
            the full command (e.g. `["radon", "cc"]`).
        """
        self.supported = supported
        self.tool_label = "tool"

    def check_supported(self, tool_name: str) -> None:
        """
        Check if a tool is supported by lintquarto.

        Parameters
        ----------
        tool_name : str
            Name of the tool to check.

        Raises
        ------
        ValueError
            If tool is not supported.

        """
        if tool_name not in self.supported:
            msg = (
                f"Unsupported {self.tool_label} '{tool_name}'. Supported: "
                f"{', '.join(self.supported.keys())}",
            )
            raise ValueError(msg)

    def check_available(self, tool_name: str) -> None:
        """
        Check if a tool is available in the user's system.

        Parameters
        ----------
        tool_name : str
            Name of the tool to check.

        Raises
        ------
        FileNotFoundError
            If the tool's command is not found in the user's PATH.

        """
        executable = self.supported[tool_name][0]
        if shutil.which(executable) is None:
            msg = (f"{executable} not found. Please install it.",)
            raise FileNotFoundError(msg)

    def status_list(self) -> list[dict[str, object]]:
        """
        Return list of availability of all supported tools.

        Returns
        -------
        list[dict[str, object]]
            List of dictionaries with tool name and availability.
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


class Linters(ToolRegistry):
    """Registry of supported linters (and code analysis tools)."""

    def __init__(self) -> None:
        super().__init__(
            {
                "flake8": ["flake8"],
                "mypy": ["mypy"],
                "pycodestyle": ["pycodestyle"],
                "pydoclint": ["pydoclint"],
                "pyflakes": ["pyflakes"],
                # Disable missing module docstring (C0114)- irrelevant for qmd
                "pylint": ["pylint", "--disable=C0114"],
                "pyright": ["pyright"],
                "pyrefly": ["pyrefly", "check"],
                "pytype": ["pytype"],
                # To compute cyclomatic complexity
                "radon-cc": ["radon", "cc"],
                # To compute maintainability index
                "radon-mi": ["radon", "mi"],
                # To compute raw metrics
                "radon-raw": ["radon", "raw"],
                # To compute halstead metrics
                "radon-hal": ["radon", "hal"],
                # Specify linter and disable irrelevant checks
                "ruff": [
                    "ruff",
                    "check",
                    "--config",
                    "lint.ignore = ['RUF100', 'INP001']",
                ],
                "vulture": ["vulture"],
            }
        )
        self.tool_label = "linter"


class Formatters(ToolRegistry):
    """Registry of supported code formatters.

    Attributes
    ----------
    check_only : set[str]
        Names of formatters that only check formatting without modifying files.
        For these formatters, ``format_qmd`` skips the write-back step.
    """

    def __init__(self) -> None:
        super().__init__(
            {
                "ruff-format": ["ruff", "format"],
                "ruff-format-check": ["ruff", "format", "--check"],
                "ruff-check-fix": ["ruff", "check", "--fix"],
            }
        )
        self.tool_label = "formatter"
        self.check_only: set[str] = {"ruff-format-check"}
