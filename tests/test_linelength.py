"""Unit tests for the linelength module."""

import configparser
import tempfile
from pathlib import Path

import pytest
import toml

from lintquarto.linelength import LineLengthDetector

# =============================================================================
# 1. Default value detection
# =============================================================================


@pytest.mark.parametrize(
    ("linter", "expected"),
    [("flake8", 79)],
)
def test_default_line_length(linter, expected):
    """Test that default line length is returned when no config files exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        detector = LineLengthDetector(linter, start_dir=tmpdir)
        assert detector.get_line_length() == expected


# =============================================================================
# 2. Config file detection for flake8
# =============================================================================


@pytest.mark.parametrize(
    ("linter", "config_file"),
    [
        ("flake8", ".flake8"),
        ("flake8", "tox.ini"),
    ],
)
def test_config_detection(linter, config_file):
    """Test detection of line length from various config files."""
    # Create config file with max-line-length set
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / config_file
        config = configparser.ConfigParser()
        config.add_section(linter)
        config.set(linter, "max-line-length", "200")
        with config_path.open("w", encoding="utf-8") as f:
            config.write(f)

        # Check if the line length was detected
        detector = LineLengthDetector(linter, start_dir=tmpdir)
        assert detector.get_line_length() == 200


def test_config_precedence():
    """Test that the first config file found in the search order is used."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create path to two config files in the same directory
        flake8_path = Path(tmpdir) / ".flake8"
        setup_cfg_path = Path(tmpdir) / "setup.cfg"

        # Create .flake8 config file
        config1 = configparser.ConfigParser()
        config1.add_section("flake8")
        config1.set("flake8", "max-line-length", "111")
        with flake8_path.open("w", encoding="utf-8") as f:
            config1.write(f)

        # Create setup.cfg
        config2 = configparser.ConfigParser()
        config2.add_section("flake8")
        config2.set("flake8", "max-line-length", "222")
        with setup_cfg_path.open("w", encoding="utf-8") as f:
            config2.write(f)

        # Check that the value from .flake8 is used
        detector = LineLengthDetector("flake8", start_dir=tmpdir)
        assert detector.get_line_length() == 111


def test_config_parent_directory():
    """Test that config files in parent directories are found."""
    # Create config file
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / ".flake8"
        config = configparser.ConfigParser()
        config.add_section("flake8")
        config.set("flake8", "max-line-length", "123")
        with config_path.open("w", encoding="utf-8") as f:
            config.write(f)

        # Run detector from sub-directory and check that file was found
        subdir = Path(tmpdir) / "subdir"
        Path(subdir).mkdir()
        detector = LineLengthDetector("flake8", start_dir=subdir)
        assert detector.get_line_length() == 123


@pytest.mark.parametrize("invalid_value", ["notanumber", "", " "])
def test_config_invalid(invalid_value):
    """Test that invalid config values are ignored and default is used."""
    # Create config file with invalid values
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / ".flake8"
        config = configparser.ConfigParser()
        config.add_section("flake8")
        config.set("flake8", "max-line-length", invalid_value)
        with config_path.open("w", encoding="utf-8") as f:
            config.write(f)

        # Confirm that the default value was used
        detector = LineLengthDetector("flake8", start_dir=tmpdir)
        assert detector.get_line_length() == 79

