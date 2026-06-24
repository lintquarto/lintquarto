"""Read `[tool.lintquarto]` configuration from `pyproject.toml`."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import toml

# =============================================================================
# Main function: find pyproject.toml and load arguments
# =============================================================================


def load_config(start_dir: str | Path = ".") -> LintquartoConfig:
    """
    Load `[tool.lintquarto]` settings from the nearest `pyproject.toml`.

    Parameters
    ----------
    start_dir : str | Path, optional
        Directory from which to begin the search. Defaults to the current
        working directory.

    Returns
    -------
    LintquartoConfig
        Parsed configuration. All fields default to empty lists or `False`
        when not specified.
    """
    pyproject_path = find_pyproject_toml(start_dir)
    if pyproject_path is None:
        return LintquartoConfig()

    try:
        with pyproject_path.open(encoding="utf-8") as f:
            data = toml.load(f)
    except Exception:  # noqa: BLE001
        # Use defaults if the file cannot be read or parsed
        return LintquartoConfig()

    section = data.get("tool", {}).get("lintquarto", {})
    if not section:
        return LintquartoConfig()

    return LintquartoConfig(
        linters=_str_list(section, "linters"),
        formatters=_str_list(section, "formatters"),
        paths=_str_list(section, "paths"),
        exclude=_str_list(section, "exclude"),
        lint_non_exec=_bool(section, "lint-non-exec"),
        verbose=_bool(section, "verbose"),
        keep_temp=_bool(section, "keep-temp"),
        custom_commands=_str_list(section, "custom-commands"),
        config_path=pyproject_path,
    )


# =============================================================================
# Find nearest pyproject.toml file
# =============================================================================


def find_pyproject_toml(start_dir: str | Path = ".") -> Path | None:
    """
    Walk up the directory tree to find a `pyproject.toml` file.

    Parameters
    ----------
    start_dir : str | Path, optional
        Directory from which to begin searching. Defaults to the current
        working directory.

    Returns
    -------
    Path | None
        Resolved path to the first `pyproject.toml` found, or `None` if
        none exists in the tree.
    """
    current = Path(start_dir).resolve()

    while True:
        candidate = current / "pyproject.toml"
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            return None

        # Reached neither a config file nor the filesystem root yet,
        # so continue searching in the parent directory
        current = parent


# =============================================================================
# Blank configuration template
# =============================================================================


@dataclass
class LintquartoConfig:
    """
    Configuration parsed from `[tool.lintquarto]` in `pyproject.toml`.

    Attributes
    ----------
    linters : list[str]
        Linter names to run. Equivalent to `-l` / `--linters`.
    formatters : list[str]
        Formatters to run. Equivalent to `-f` / `--formatters`.
    paths : list[str]
        Files and/or directories to run tools on. Equivalent to
        `-p` / `--paths`.
    exclude : list[str]
        Files and/or directories to exclude from running tools on. Equivalent
        to `-e` / `--exclude`.
    lint_non_exec : bool
        If `True`, also lint non-executable Python code chunks. Equivalent to
        `-n` / `--lint-non-exec`.
    verbose : bool
        If `True`, print detailed progress information. Equivalent to `-v` /
        `--verbose`.
    keep_temp : bool
        If `True`, retain temporary `.py` files after linting. Equivalent to
        `-k` / `--keep-temp`.
    custom_commands : list[str]
        Custom commands to run against the generated `.py` file. Equivalent to
        `-c` / `--custom-commands`.
    config_path : Path | None
        Path to the `pyproject.toml` file that was read, or `None` if no
        file was found.

    """

    linters: list[str] = field(default_factory=list)
    formatters: list[str] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    lint_non_exec: bool = False
    verbose: bool = False
    keep_temp: bool = False
    custom_commands: list[str] = field(default_factory=list)
    config_path: Path | None = None


# =============================================================================
# Helpers used when extracting information from pyproject.toml
# =============================================================================


def _str_list(section: dict, key: str) -> list[str]:
    """
    Extract a list[str] from `section`, silently ignoring bad values.

    Parameters
    ----------
    section : dict
        Mapping containing configuration values from `[tool.lintquarto]`.
    key : str
        Name of the configuration field to read.

    Returns
    -------
    list[str]
        Value for `key` converted to a list of strings when the underlying
        value is a list, otherwise an empty list.
    """
    raw = section.get(key, [])
    if isinstance(raw, list):
        return [str(item) for item in raw]
    return []


def _bool(section: dict, key: str, *, default: bool = False) -> bool:
    """
    Extract a boolean from `section`.

    Parameters
    ----------
    section : dict
        Mapping containing configuration values from `[tool.lintquarto]`.
    key : str
        Name of the configuration field to read.
    default : bool, optional
        Value to return when `key` is missing or does not contain a boolean.
        Defaults to `False`.

    Returns
    -------
    bool
        Boolean value stored under `key`, or `default` when the stored value
        is missing or not a boolean.
    """
    raw = section.get(key, default)
    if isinstance(raw, bool):
        return raw
    return default
