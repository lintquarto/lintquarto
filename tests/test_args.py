"""
Unit tests for the args module.
"""

import pytest

from lintquarto.args import CustomArgumentParser


def test_error_prints_custom_message_and_exits(capsys):
    """
    Test that CustomArgumentParser prints a custom error message to stderr,
    prints help text to stdout, and exits with code 2 when required arguments
    are missing.

    Mimics real-world usage where a user forgets to provide a required
    argument. The parser internally calls its `error()` method when it detects
    the missing argument.

    Parameters
    ----------
    capsys : _pytest.capture.CaptureFixture
        Pytest fixture to capture output to stdout and stderr.

    Raises
    ------
    AssertionError
        If the error message or help text are not found in the expected output
        streams, or if the exit code is not 2.
    """
    # Create parser and add a required argument
    parser = CustomArgumentParser(prog="prog")
    parser.add_argument('--foo', required=True)

    # Simulate missing required argument to trigger the error method
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args([])

    # Check that the exit code is 2
    assert excinfo.value.code == 2

    # Capture output from stderr and stdout
    captured = capsys.readouterr()

    # Confirm the custom error message is in stderr
    stderr_msg = "❌ Error: the following arguments are required: --foo"
    assert stderr_msg in captured.err

    # Confirm the help text is in stdout
    assert "usage: prog" in captured.out


def test_error_method_directly(capsys):
    """
    Test that calling the error() method directly prints the custom error
    message to stderr, prints help text to stdout, and exits with code 2.

    Directly calls the `error()` method to ensure it behaves as expected,
    regardless of how it's triggered. Useful for unit testing the method
    itself, independent of argument parsing logic.

    Parameters
    ----------
    capsys : _pytest.capture.CaptureFixture
        Pytest fixture to capture output to stdout and stderr.

    Raises
    ------
    AssertionError
        If the error message or help text are not found in the expected output
        streams, or if the exit code is not 2.
    """
    # Create parser instance
    parser = CustomArgumentParser(prog="prog")

    # Call the error method directly with a custom message
    with pytest.raises(SystemExit) as excinfo:
        parser.error("custom error message")

    # Check that the exit code is 2
    assert excinfo.value.code == 2

    # Capture output from stderr and stdout
    captured = capsys.readouterr()

    # Confirm the custom error message is in stderr
    assert "❌ Error: custom error message" in captured.err

    # Confirm the help text is in stdout
    assert "usage: prog" in captured.out
