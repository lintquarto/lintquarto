"""Run tool on list of QMD files."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

from .processing import format_qmd, process_qmd


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
            runner=process_qmd,
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
            runner=process_qmd,
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
