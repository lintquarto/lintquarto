"""Convert .qmd file to python file."""

import re
import warnings

from pathlib import Path
from typing import List, Union, Optional

from .args import CustomArgumentParser
from .linelength import LineLengthDetector
from .linters import Linters


class QmdToPyConverter:
    """
    Convert lines from a .qmd file to .py file.

    Attributes
    ----------
    in_chunk_options : bool
        True if currently at the start of a code chunk, parsing Quarto chunk
        options or leading blank lines.
    in_python : bool
        True if currently processing lines inside a Python code chunk.
    py_lines : list
        Stores the lines to be written to the output Python file.
    """
    in_chunk_options: bool = False
    in_python: bool = False
    py_lines: list = []

    def __init__(self, linter: str) -> None:
        """
        Initialise a class object.

        Parameters
        ----------
        linter : str
            Name of the linter that will be used.
        """
        self.linter = linter

        # Check the linter is supported
        Linters().check_supported(self.linter)

        # Determine whether to preserve line count
        if self.linter == "radon-raw":
            self.preserve_line_count = False
        else:
            self.preserve_line_count = True

        # Determine if linter uses noqa, and so find max line length
        self.uses_noqa = self.linter in ["flake8", "ruff", "pycodestyle"]
        if self.uses_noqa:
            len_detect = LineLengthDetector(linter=self.linter)
            self.max_line_length = len_detect.get_line_length()

    def reset(self) -> None:
        """
        Reset the state (except linter).
        """
        self.py_lines = []
        self.in_python = False
        self.in_chunk_options = False

    def convert(self, qmd_lines: List[str]) -> List[str]:
        """
        Run converter on the provided lines.

        Parameters
        ----------
        qmd_lines : List[str]
            List containing each line from the Quarto file.

        Returns
        -------
        py_lines : List[str]
            List of each line for the output Python file.
        """
        self.reset()
        for original_line in qmd_lines:
            self.process_line(original_line)
        return self.py_lines

    def process_line(self, original_line: str) -> None:
        """
        Process individual lines with state tracking.

        Parameters
        ----------
        original_line : str
            Line to process.
        """
        # Remove the trailing new line
        line = original_line.rstrip("\n")

        # Check if it is the start of a python code chunk (allowing spaces
        # before {python} and allowing chunk options e.g. {python, echo=...})
        if re.match(r"^```\s*{python[^}]*}$", line):
            self.in_python = True
            self.in_chunk_options = True
            if self.preserve_line_count:
                self.py_lines.append("# %% [python]")

        # Check if it is the end of a code chunk
        elif line.strip() == "```":
            self.in_python = False
            self.in_chunk_options = False
            if self.preserve_line_count:
                self.py_lines.append("# -")

        # Check if it is within a python code chunk
        elif self.in_python:
            self._handle_python_chunk(line)

        # For all other lines, set to # -
        else:
            if self.preserve_line_count:
                self.py_lines.append("# -")

    def _handle_python_chunk(self, line: str) -> None:
        """
        Process a line within a Python code chunk.

        Parameters
        ----------
        line : str
            The line to process.

        Returns
        -------
        None
        """
        # After the first code line, append all lines unchanged (with handling
        # for quarto include syntax and code annotations)
        if not self.in_chunk_options:
            line = self._handle_includes(line)
            line = self._handle_annotations(line)
            self.py_lines.append(line)
            return

        # If line is blank, just append it
        if line.strip() == "":
            self.py_lines.append(line)
            return

        # Remove blank space at start of line
        stripped = line.lstrip()

        # If line is a quarto chunk option, only append when preserving lines
        # and suppress E265 (as will warn for "#|" comment spacing)
        if stripped.startswith("#| "):
            if not self.preserve_line_count:
                return
            if self.uses_noqa:
                line = self._add_noqa(line, ["E265"])
            self.py_lines.append(line)
            return

        # If line is a comment, just append it (but handle code annotations)
        if stripped.startswith("#"):
            line = self._handle_annotations(line)
            self.py_lines.append(line)
            return

        # Identified this as first code line after options/blanks/comments...

        # Handle quarto include syntax and code annotations
        line = self._handle_includes(line)
        line = self._handle_annotations(line)

        # Always suppress E305, and suppress E302 if it is a function or class
        if self.uses_noqa:
            is_def_or_class = re.match(r"^(def|class)\b", stripped)
            if is_def_or_class:
                line = self._add_noqa(line, ["E302", "E305"])
            else:
                line = self._add_noqa(line, ["E305"])

        self.py_lines.append(line)
        self.in_chunk_options = False

    def _add_noqa(self, line: str, suppress: list) -> str:
        """
        Add noqa suppressions to the line, plus E501 for short lines.

        E501 is add to lines that do not already exceed the max line length, as
        the noqa comment itself may cause the final line to exceed the limit.

        Parameters
        ----------
        line : str
            The line to process.
        suppress : list
            List of noqa flags to add.

        Returns
        -------
        str
            The input line with 'noqa' suppressions appended as a comment.
        """
        if len(line) <= self.max_line_length:
            suppress.append("E501")
        return f"{line.rstrip()}  # noqa: {','.join(suppress)}"

    def _handle_includes(self, line: str) -> str:
        """
        Comment line if it contains Quarto include syntax
        ("{{< include ... >}}").

        Parameters
        ----------
        line : str
            The line to process.

        Returns
        -------
        str
            The input line, but commented if it had quarto include syntax.
        """
        if (
            line.lstrip().startswith("{{< include ")
            and line.rstrip().endswith(">}}")
        ):
            return f"# {line}"
        return line

    def _handle_annotations(self, line: str) -> str:
        """
        Remove in-line quarto code annotations ("#<<").

        These are placed at the end of a line for shafayetShafee's
        line-highlight extension. If found, "#<<" and any whitespace before it
        are stripped from the end of the line.

        Parameters
        ----------
        line : str
            The line to process.

        Returns
        -------
        str
            The line with trailing whitespace and any "#<<" at the end removed.
        """
        return re.sub(r"\s*#<<\s*$", "", line)


def get_unique_filename(path: Union[str, Path]) -> Path:
    """
    Generate a unique file path by appending " (n)" before the file extension
    if needed.

    If the given path already exists, this function appends an incrementing
    number in parentheses before the file extension (e.g., "file (1).py") until
    an unused filename is found.

    Parameters
    ----------
    path : Union[str, Path]
        The initial file path to check.

    Returns
    -------
    Path
        A unique file path that does not currently exist.

    Examples
    --------
    >>> get_unique_filename("script.py")
    PosixPath('script.py')  # if 'script.py' does not exist
    >>> get_unique_filename("script.py")
    PosixPath('script (1).py')  # if 'script.py' exists
    """
    path = Path(path)
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    n = 1
    while True:
        new_name = f"{stem} ({n}){suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        n += 1


def convert_qmd_to_py(
    qmd_path: Union[str, Path],
    linter: str,
    output_path: Optional[Union[str, Path]] = None,
    verbose: bool = False
) -> Optional[Path]:
    """
    Convert a Quarto (.qmd) file to Python (.py) file, preserving line
    alignment.

    Parameters
    ----------
    qmd_path : Union[str, Path]
        Path to the input .qmd file.
    linter : str
        Name of the linter that will be used.
    output_path : Optional[Union[str, Path]]
        Path for the output .py file. If None, uses qmd_path with .py suffix.
    verbose : bool, optional
        If True, print detailed progress information.

    Returns
    -------
    output_path : Optional[Path]
        Path for the output .py file, or None if there was an error.

    Examples
    --------
    >>> convert_qmd_to_py("input.qmd", "output.py", True)
    # To use from the command line:
    # $ python converter.py input.qmd [output.py] [-v]
    """
    # Convert input path to a Path object
    qmd_path = Path(qmd_path)

    # Set up converter
    converter = QmdToPyConverter(linter=linter)

    # Determine output path. If provided, convert to a Path object. If not,
    # the file extension of the input file to `.py`
    if output_path is None:
        output_path = qmd_path.with_suffix(".py")
    else:
        output_path = Path(output_path)

    # Automatically generate a unique filename if needed
    output_path = get_unique_filename(output_path)

    if verbose:
        print(f"Converting {qmd_path} to {output_path}")

    try:
        # Open and read the QMD file, storing all lines in qmd_lines
        with open(qmd_path, "r", encoding="utf-8") as f:
            qmd_lines = f.readlines()

        # Iterate over lines, keeping python code, and setting rest to "# -"
        py_lines = converter.convert(qmd_lines=qmd_lines)

        # Write the output file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(py_lines) + "\n")

        if verbose:
            print(f"✓ Successfully converted {qmd_path} to {output_path}")

        # Check that line counts match (if intend to preserve them)
        if converter.preserve_line_count:
            qmd_len = len(qmd_lines)
            py_len = len(py_lines)
            if qmd_len == py_len:
                if verbose:
                    print(f"  Line count: {qmd_len} → {py_len} ")
            else:
                warnings.warn(f"Line count mismatch: {qmd_len} → {py_len}",
                              RuntimeWarning)

    # Error messages if issues finding/accessing files, or otherwise.
    except FileNotFoundError:
        print(f"Error: Input file '{qmd_path}' not found")
        return None
    except PermissionError:
        print(f"Error: Permission denied accessing '{qmd_path}' "
              f"or '{output_path}'")
        return None
    # Intentional broad catch for unexpected conversion errors
    # pylint: disable=broad-except
    except Exception as e:
        print(f"Error during conversion: {e}")
        return None
    return output_path


# To ensure it executes if run from terminal:
if __name__ == "__main__":

    # Set up argument parser with help statements
    parser = CustomArgumentParser(
        description="Convert .qmd file to python file.")
    parser.add_argument("qmd_path", help="Path to the input .qmd file.")
    parser.add_argument("output_path", nargs="?", default=None,
                        help="(Optional) path to the output .py file.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Print detailed progress information.")
    args = parser.parse_args()

    # Pass arguments to function and run it
    convert_qmd_to_py(args.qmd_path, args.output_path, args.verbose)
