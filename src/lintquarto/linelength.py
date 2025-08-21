"""Detect configured line length."""

import configparser
import os
from typing import Optional

import toml


# pylint: disable=too-few-public-methods
class LineLengthDetector:
    """
    Detect the configured line length for a given Python linter.

    This class searches for relevant configuration files in the directory tree,
    extracts the maximum line length setting for the specified linter, and
    returns the default value if no configuration is found.

    Attributes
    ----------
    defaults : dict
        The default maximum line length for each linter.
    """
    defaults: dict = {
        "flake8": 79,
        "pycodestyle": 79,
        "ruff": 88
    }

    def __init__(self, linter: str, start_dir: str = ".") -> None:
        """
        Initialise a class object.

        Parameters
        ----------
        linter : str
            The name of the linter to check ("flake8", "pycodestyle", "ruff").
        start_dir : str, optional
            The directory from which to start searching for configuration
            files. Defaults to the current directory.

        Raises
        ------
        ValueError
            If the specified linter is not supported.
        """
        self.linter = linter
        if self.linter not in self.defaults:
            raise ValueError(
                f"LineLengthDetector not available for {self.linter}. ",
                f"Can only check: {self.defaults.keys()}.")
        self.start_dir = os.path.abspath(start_dir)

    def get_line_length(self) -> int:
        """
        Get the configured maximum line length for the specified linter.

        Returns
        -------
        int
            The maximum line length.
        """
        if self.linter in ["flake8", "pycodestyle"]:
            return self._get_flake8_line_length()
        if self.linter == "ruff":
            return self._get_ruff_line_length()
        return self.defaults[self.linter]

    def _get_flake8_line_length(self) -> int:
        """
        Search for the maximum line length in Flake8-compatible configuration
        files.

        This method checks `.flake8`, `setup.cfg`, and `tox.ini` files for the
        `max-line-length` option under `[flake8]` or `[pycodestyle]` sections.

        Returns
        -------
        int
            The maximum line length.
        """
        config_files = [".flake8", "setup.cfg", "tox.ini"]
        current = self.start_dir
        while True:
            # Iterate over possible config files in the current directory
            for config_file in config_files:
                path = os.path.join(current, config_file)
                if not os.path.isfile(path):
                    continue  # Skip if file does not exist
                config = configparser.ConfigParser()
                config.read(path)
                # Try to extract line length from the config
                length = self._extract_line_length_from_config(config)
                if length is not None:
                    return length  # Return as soon as a value is found
            # Move up to the parent directory
            parent = os.path.dirname(current)
            if parent == current:
                break  # Stop if we've reached the filesystem root
            current = parent
        # Return default if no config value is found
        return self.defaults[self.linter]

    def _extract_line_length_from_config(
        self,
        config: configparser.ConfigParser
    ) -> Optional[int]:
        """
        Extract the maximum line length from a configparser.ConfigParser
        object.

        This helper checks both the `[flake8]` and `[pycodestyle]` sections for
        a `max-line-length` option. If found, it attempts to convert the value
        to an integer and return it. If the value is missing or invalid,
        returns None.

        Parameters
        ----------
        config : configparser.ConfigParser
            The parsed configuration object.

        Returns
        -------
        Optional[int]
            The extracted line length, or None if not found or invalid.
        """
        for section in ["flake8", "pycodestyle"]:
            # Check if section and option exist
            if (
                config.has_section(section)
                and config.has_option(section, "max-line-length")
            ):
                try:
                    # Attempt to parse and return the integer value
                    return int(config.get(section, "max-line-length"))
                except (ValueError, configparser.Error):
                    # Ignore invalid values or config errors and keep searching
                    pass
        # Return None if no valid value is found
        return None

    def _get_ruff_line_length(self) -> int:
        """
        Search for the maximum line length in `pyproject.toml` for Ruff.

        This method checks the `[tool.ruff]` section for the `line-length`
        option.

        Returns
        -------
        int
            The maximum line length.
        """
        current = self.start_dir
        while True:
            path = os.path.join(current, "pyproject.toml")
            if os.path.isfile(path):
                try:
                    config = toml.load(path)
                    ruff_config = config.get("tool", {}).get("ruff", {})
                    if "line-length" in ruff_config:
                        return int(ruff_config["line-length"])
                except (toml.TomlDecodeError, OSError, ValueError):
                    # Ignore parse errors, file errors, or invalid values
                    pass
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        return self.defaults[self.linter]
