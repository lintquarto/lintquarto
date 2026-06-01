"""Retrieving linters."""

import shutil
from pathlib import Path
from typing import Any, Optional, Union


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
            "ruff": ["ruff", "check"],  # To specify linter (not formatter)
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

    def ruff_has_config(
        self, original_source: Path, return_path: bool = False
    ) -> Optional[dict[str, Any]]:
        """Walk up the directory tree to find a valid local Ruff config file.

        Follows the same path finding logic as defined in Ruff's documentation:
        https://docs.astral.sh/ruff/configuration/#config-file-discovery

        Order of precedence is `.ruff.toml` > `ruff.toml` > `pyproject.toml`.
        The `pyproject.toml` file is only considered a match if it contains a
        `[tool.ruff]` block.

        Parameters
        ----------
        original_source : pathlib.Path
            The starting file or directory path from which to begin searching
            upwards.
        return_path : bool, default False
            If True, returns the `pathlib.Path` object of the located
            configuration file instead of a boolean value.

        Returns
        -------
        bool or pathlib.Path
            If `return_path` is False: Returns True if a configuration file is
            found, False otherwise.
            If `return_path` is True: Returns the Path to the configuration
            file if found, False otherwise.

        See Also
        --------
        build_ruff_args : Leverages this method to determine fallback
            arguments.
        """

        def _found(path: Path) -> Union[bool, Path]:
            return path if return_path else True

        current = original_source.resolve()

        if current.is_file():
            current = current.parent

        while True:
            # Check for standalone Ruff config files
            config = current / ".ruff.toml"
            if (current / ".ruff.toml").is_file():
                return _found(config)

            config = current / "ruff.toml"
            if (current / "ruff.toml").is_file():
                return _found(config)

            # Check for pyproject.toml containing a [tool.ruff] section
            config = current / "pyproject.toml"
            if config.is_file():
                try:
                    if "[tool.ruff]" in config.read_text(encoding="utf-8"):
                        return _found(config)
                except (OSError, UnicodeDecodeError):
                    # Handle rare errors relating to permissions etc.
                    # gracefully
                    # OSError covers PermissionError, FileNotFoundError, etc.
                    # UnicodeDecodeError covers malformed file encoding.
                    # If any of these happen, keep walking trying to find
                    # a valid file
                    pass

            # Walk upstairs
            parent = current.parent
            if (
                parent == current
            ):  # Reached the root directory (e.g., C:\ or /)
                break
            current = parent

        return False

    def build_ruff_args(self, target: Path) -> list[str]:
        """Construct CLI arguments for Ruff based on local config presence.

        Checks if a valid local configuration file exists for the given target.
        If no configuration is discovered upstream, it provides a default set
        of fallback arguments to ignore specific rules (`RUF100`, `INP001`).

        Parameters
        ----------
        target : pathlib.Path
            The file path currently being targeted for linting.

        Returns
        -------
        list of str
            A list of command-line argument strings to pass to the Ruff CLI.
            Returns an empty list if a local configuration is found.

        See Also
        --------
        ruff_has_config :
            The underlying method used to discover configuration files.
        """
        if not self.ruff_has_config(target):
            return ["--config", "lint.ignore = ['RUF100', 'INP001']"]

        return []
