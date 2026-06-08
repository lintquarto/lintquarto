"""Tests for config.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from lintquarto.config import find_pyproject_toml, load_config


def _write_pyproject(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "pyproject.toml"
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# find_pyproject_toml
# ---------------------------------------------------------------------------


def test_find_pyproject_toml_present(tmp_path: Path) -> None:
    """Finds pyproject.toml if present in current path."""
    p = _write_pyproject(tmp_path, "")
    assert find_pyproject_toml(tmp_path) == p


def test_find_pyproject_toml_absent(tmp_path: Path) -> None:
    """No pyproject.toml identified if none is present."""
    assert find_pyproject_toml(tmp_path) is None


def test_find_pyproject_toml_parent(tmp_path: Path) -> None:
    """Finds pyproject.toml from parent."""
    p = _write_pyproject(tmp_path, "")
    child = tmp_path / "a" / "b"
    child.mkdir(parents=True)
    assert find_pyproject_toml(child) == p


# ---------------------------------------------------------------------------
# load_config - absence / malformed
# ---------------------------------------------------------------------------


def test_load_config_no_file(tmp_path: Path) -> None:
    """Returns empty config when no pyproject.toml exists."""
    cfg = load_config(tmp_path)
    assert cfg.linters == []
    assert cfg.paths == []
    assert cfg.exclude == []
    assert cfg.lint_non_exec is False
    assert cfg.verbose is False
    assert cfg.keep_temp is False
    assert cfg.custom_commands == []
    assert cfg.config_path is None


def test_load_config_no_lintquarto_section(tmp_path: Path) -> None:
    """Returns empty config when pyproject.toml has no [tool.lintquarto]."""
    _write_pyproject(tmp_path, "[tool.ruff]\nline-length = 88\n")

    cfg = load_config(tmp_path)
    assert cfg.linters == []
    assert cfg.config_path is None


def test_load_config_invalid_toml(tmp_path: Path) -> None:
    """Returns empty config silently when pyproject.toml is malformed."""
    (tmp_path / "pyproject.toml").write_text(
        "not : valid toml !!!", encoding="utf-8"
    )

    cfg = load_config(tmp_path)
    assert cfg.linters == []
    assert cfg.config_path is None


# ---------------------------------------------------------------------------
# load_config - full and partial sections
# ---------------------------------------------------------------------------


def test_load_config_full_section(tmp_path: Path) -> None:
    """Parses all fields correctly from a fully-specified section."""
    _write_pyproject(
        tmp_path,
        "[tool.lintquarto]\n"
        'linters = ["ruff", "pycodestyle"]\n'
        'paths = ["examples/", "dashboard/index.qmd"]\n'
        'exclude = ["badfile.qmd"]\n'
        "lint-non-exec = true\n"
        "verbose = true\n"
        "keep-temp = true\n"
        'custom-commands = ["mytool --flag"]\n',
    )

    cfg = load_config(tmp_path)
    assert cfg.linters == ["ruff", "pycodestyle"]
    assert cfg.paths == ["examples/", "dashboard/index.qmd"]
    assert cfg.exclude == ["badfile.qmd"]
    assert cfg.lint_non_exec is True
    assert cfg.verbose is True
    assert cfg.keep_temp is True
    assert cfg.custom_commands == ["mytool --flag"]
    assert cfg.config_path == tmp_path / "pyproject.toml"


def test_load_config_partial_section(tmp_path: Path) -> None:
    """Missing keys default to empty list or False."""
    _write_pyproject(tmp_path, '[tool.lintquarto]\nlinters = ["flake8"]\n')

    cfg = load_config(tmp_path)
    assert cfg.linters == ["flake8"]
    assert cfg.paths == []
    assert cfg.lint_non_exec is False
    assert cfg.custom_commands == []


def test_load_config_boolean_defaults_false(tmp_path: Path) -> None:
    """Boolean flags default to False when absent from config."""
    _write_pyproject(tmp_path, '[tool.lintquarto]\nlinters = ["ruff"]\n')
    cfg = load_config(tmp_path)
    assert cfg.verbose is False
    assert cfg.keep_temp is False
    assert cfg.lint_non_exec is False


# ---------------------------------------------------------------------------
# load_config - directory walking
# ---------------------------------------------------------------------------


def test_load_config_walks_up(tmp_path: Path) -> None:
    """Finds pyproject.toml in a parent directory."""
    _write_pyproject(tmp_path, '[tool.lintquarto]\nlinters = ["mypy"]\n')
    nested = tmp_path / "sub" / "dir"
    nested.mkdir(parents=True)

    cfg = load_config(nested)
    assert cfg.linters == ["mypy"]
    assert cfg.config_path == tmp_path / "pyproject.toml"


def test_load_config_nearest_wins(tmp_path: Path) -> None:
    """Closer pyproject.toml takes precedence over one higher up."""
    _write_pyproject(tmp_path, '[tool.lintquarto]\nlinters = ["flake8"]\n')
    child = tmp_path / "sub"
    child.mkdir()
    _write_pyproject(child, '[tool.lintquarto]\nlinters = ["ruff"]\n')

    cfg = load_config(child)
    assert cfg.linters == ["ruff"]
