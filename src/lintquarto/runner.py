"""Run tool on list of QMD files."""

from __future__ import annotations

import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

from .convert.converter import convert_qmd_to_py
from .convert.rebuild_qmd import recreate_qmd_from_formatted_py
from .registry import Formatters, Linters

# =============================================================================
# Main class - gets settings, then calls lint_qmd or format_qmd to run across
# across all files
# =============================================================================


class ToolRunner:
    """
    Run built-in and custom tools across a set of Quarto files.

    Attributes
    ----------
    qmd_files : list[str]
        List of paths to `.qmd` files to process.
    keep_temp : bool
        If True, keep temporary Python files.
    verbose : bool
        If True, print progress messages during execution.
    lint_non_exec : bool
        If True, also process non-executable Python code chunks.
    """

    def __init__(
        self,
        qmd_files: list[str],
        *,
        keep_temp: bool,
        verbose: bool,
        lint_non_exec: bool,
    ) -> None:
        """
        Initialise ToolRunner.

        Parameters
        ----------
        qmd_files : list[str]
            List of paths to `.qmd` files to process.
        keep_temp : bool
            If True, keep temporary Python files.
        verbose : bool
            If True, print progress messages during execution.
        lint_non_exec : bool
            If True, also process non-executable Python code chunks.
        """
        self.qmd_files = qmd_files
        self.keep_temp = keep_temp
        self.verbose = verbose
        self.lint_non_exec = lint_non_exec

    def run_formatter(self, formatter: str) -> int:
        """
        Run one built-in formatter across all qmd files.

        Parameters
        ----------
        formatter : str
            Name of formatter to run.
        """
        return self._run_across_files(
            label=formatter,
            runner=format_qmd,
            formatter=formatter,
        )

    def run_linter(self, linter: str) -> int:
        """
        Run one built-in linter across all qmd files.

        Parameters
        ----------
        linter : str
            Name of linter to run.
        """
        return self._run_across_files(
            label=linter,
            runner=lint_qmd,
            linter=linter,
        )

    def run_custom(self, command: list[str]) -> int:
        """
        Run one custom command across all qmd files.

        Parameters
        ----------
        command : list[str]
            Custom command, represented as list of command-line tokens.
        """
        return self._run_across_files(
            label=f"custom command: {' '.join(command)}",
            runner=lint_qmd,
            custom_command=command,
        )

    def _run_across_files(
        self,
        label: str,
        runner: Callable[..., int],
        **runner_kwargs: object,
    ) -> int:
        """
        Run a processing function across all qmd files.

        Parameters
        ----------
        label : str
            Human-readable label to print before running.
        runner : Callable[..., int]
            Function to call for each `.qmd` file.
        **runner_kwargs : object
            Extra keyword arguments forwarded to `runner`.

        Returns
        -------
        int
            Exit status. Returns 0 if all files are processed successfully,
            otherwise returns the highest non-zero exit code seen.
        """
        self._print_run_header(label)
        exit_code = 0

        for qmd_file in self.qmd_files:
            try:
                ret = runner(
                    qmd_file=qmd_file,
                    keep_temp_files=self.keep_temp,
                    verbose=self.verbose,
                    lint_non_exec=self.lint_non_exec,
                    **runner_kwargs,
                )
            except Exception as e:  # noqa: BLE001
                print(
                    f"Error: Unexpected error processing {qmd_file}: {e}",
                    file=sys.stderr,
                )
                ret = 1

            exit_code = max(exit_code, ret)

        return exit_code

    def _print_run_header(self, label: str) -> None:
        """
        Print a standard section header for a tool run.

        Parameters
        ----------
        label : str
            Name of tool being run.
        """
        print("==========================================================")
        print(f"Running {label}...")
        print("==========================================================")


# =============================================================================
# Linting...
# =============================================================================


def lint_qmd(  # noqa: PLR0913
    qmd_file: str | Path,
    linter: str | None = None,
    custom_command: list[str] | None = None,
    *,  # Subsequent arguments are keyword-only (`var=True`, not just `True`)
    keep_temp_files: bool = False,
    verbose: bool = False,
    lint_non_exec: bool = False,
) -> int:
    """
    Convert a .qmd file to .py, lint it, and clean up.

    Parameters
    ----------
    qmd_file : str | Path
        Path to the `.qmd` file to process.
    linter : str | None, optional
        Name of the linter to run.
    custom_command : str | None, optional
        Custom command to run against generated .py file.
    keep_temp_files : bool, optional
        If True, retain the temporary .py file after linting.
    verbose : bool, optional
        If True, print detailed progress information.
    lint_non_exec : bool, optional
        If True, also lint non-executable Python code chunks.

    Returns
    -------
    int
        0 on success, nonzero on error.

    """
    # Convert input to Path object
    qmd_path = Path(qmd_file)

    # Validate that the file exists and has a .qmd extension
    if not qmd_path.exists() or qmd_path.suffix != ".qmd":
        print(f"Error: {qmd_file} is not a valid .qmd file.", file=sys.stderr)
        return 1

    if (linter is None) == (custom_command is None):
        print(
            "Error: Provide exactly one of 'linter' or 'custom_command'.",
            file=sys.stderr,
        )
        return 1

    # Convert the .qmd file to a .py file
    try:
        py_file = convert_qmd_to_py(
            qmd_path=str(qmd_path),
            linter=linter,
            verbose=verbose,
            lint_non_exec=lint_non_exec,
        )
    # Catch for if the function raises an error
    except Exception as e:  # noqa: BLE001
        print(
            f"Error: Failed to convert {qmd_file} to .py: {e}",
            file=sys.stderr,
        )
        return 1

    # Catch for if the function returns None
    if py_file is None:
        print(
            f"Error: Failed to convert {qmd_file} to .py",
            file=sys.stderr,
        )
        return 1

    with temp_py_file(py_file=py_file, keep=keep_temp_files):
        try:
            if custom_command is not None:
                command = [*custom_command, str(py_file)]
            else:
                command = Linters().supported[linter] + [str(py_file)]

            # Run command on the temporary .py file and capture output
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            # Get the base filename from the full file paths
            qmd_filename = str(qmd_path.name)
            py_filename = str(py_file.name)

            # Replace all references to the .py file with the .qmd file
            result.stdout = result.stdout.replace(py_filename, qmd_filename)
            print(result.stdout, end="")

            # If there is an error - which will include some linter outputs
            # that get classed as errors - then also replace `.py` and print
            if result.stderr:
                result.stderr = result.stderr.replace(
                    py_filename, qmd_filename
                )
                print(result.stderr, file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(
                f"Error: Unexpected failure while linting {qmd_file}: {e}",
                file=sys.stderr,
            )
            return 1

    return 0


# =============================================================================
# Formatting...
# =============================================================================


def format_qmd(
    qmd_file: str | Path,
    formatter: str,
    *,
    keep_temp_files: bool = False,
    verbose: bool = False,
    lint_non_exec: bool = False,
) -> int:
    """
    Format Python code in a Quarto file.

    This converts the input `.qmd` file into a temporary formatter-friendly
    `.py` file, runs the requested formatter on it, writes the formatted Python
    code back into the original `.qmd` file.

    Parameters
    ----------
    qmd_file : str | Path
        Path to the `.qmd` file to process.
    formatter : str
        Name of the supported formatter to run.
    keep_temp_files : bool, optional
        If True, keep the temporary `.py` file after processing.
    verbose : bool, optional
        If True, print verbose progress messages.
    lint_non_exec : bool, optional
        If True, also format non-executable Python code chunks.

    Returns
    -------
    int
        0 on success, nonzero on error.
    """
    # Convert input to Path object
    qmd_path = Path(qmd_file)

    # Validate that the file exists and has a .qmd extension
    if not qmd_path.exists() or qmd_path.suffix != ".qmd":
        print(f"Error: {qmd_file} is not a valid .qmd file.", file=sys.stderr)
        return 1

    # Convert the .qmd file to a .py file
    try:
        py_file, converter = convert_qmd_to_py(
            qmd_path=str(qmd_path),
            formatter=formatter,
            verbose=verbose,
            lint_non_exec=lint_non_exec,
        )
    # Catch for if the function raises an error
    except Exception as e:  # noqa: BLE001
        print(
            f"Error: Failed to convert {qmd_file} to .py: {e}",
            file=sys.stderr,
        )
        return 1

    # Catch for if the function returns None
    if py_file is None:
        print(
            f"Error: Failed to convert {qmd_file} to .py",
            file=sys.stderr,
        )
        return 1

    with temp_py_file(py_file=py_file, keep=keep_temp_files):
        try:
            command = list(Formatters().supported[formatter])
            command.append(str(py_file))
            if verbose:
                print(f"Running command: {' '.join(command)}")
            result = subprocess.run(
                command, capture_output=True, text=True, check=False
            )
            if result.stdout:
                print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, file=sys.stderr, end="")
            if result.returncode != 0:
                return result.returncode
            recreate_qmd_from_formatted_py(
                qmd_path=qmd_path,
                py_path=py_file,
                python_blocks=converter.python_blocks,
                verbose=verbose,
            )
            if verbose:
                print(f"✓ Successfully formatted {qmd_path}")
            return 0  # noqa: TRY300

        except Exception as e:  # noqa: BLE001
            print(
                f"Error: Unexpected error formatting {qmd_path}: {e}",
                file=sys.stderr,
            )
            return 1


# =============================================================================
# Helper functions
# =============================================================================


# Arguments after * are keyword-only (`var=True`, not just `True`)
@contextmanager
def temp_py_file(py_file: Path, *, keep: bool) -> Iterator[Path]:
    """Context manager that ensures file is removed on exit unless keep=True.

    Parameters
    ----------
    py_file : Path
        Path to the .py file.
    keep : bool
        Whether to keep the temporary .py file.
    """
    try:
        # Execution of the "with" block runs here, using py_file
        yield py_file
    # Everything after yield runs unconditionally when the with block exits
    # (whether normally, via return, or via an unhandled exception).
    finally:
        if not keep and py_file.exists():
            try:
                py_file.unlink()
            except Exception as e:  # noqa: BLE001
                print(
                    f"Warning: Could not remove temporary file {py_file}: {e}",
                    file=sys.stderr,
                )
