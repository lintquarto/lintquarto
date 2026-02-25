"""Convert .qmd file to python file"""

from pathlib import Path
import re
from typing import List, Union, Optional
import warnings

import yaml

from .args import CustomArgumentParser
from .linelength import LineLengthDetector
from .linters import Linters


# pylint: disable=too-many-instance-attributes
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
    yaml_eval_default : bool
        Default eval setting from YAML front matter.
    current_chunk_eval : Optional[bool]
        Eval setting for current chunk from chunk options (None if not set).
    """
    in_chunk_options: bool = False
    in_python: bool = False
    py_lines: list = []
    yaml_eval_default: bool = True
    current_chunk_eval: Optional[bool] = None

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
        Reset the state (except linter and YAML eval default).
        """
        self.in_chunk_options = False
        self.in_python = False
        self.py_lines = []
        self.current_chunk_eval = None

    def parse_yaml_front_matter(self, qmd_lines: List[str]) -> None:
        """
        Parse YAML front matter and extract execute.eval setting.

        Parameters
        ----------
        qmd_lines : List[str]
            List containing each line from the Quarto file.

        Returns
        -------
        None
            Stores the eval setting in self.yaml_eval_default attribute.
            Sets to True if no YAML front matter is found or if parsing fails.
        """
        # No YAML front matter detected
        if not qmd_lines or not qmd_lines[0].strip() == "---":
            self.yaml_eval_default = True
            return

        yaml_lines = []

        # Find the end of YAML front matter
        for i in range(1, len(qmd_lines)):
            if qmd_lines[i].strip() == "---":
                break
            yaml_lines.append(qmd_lines[i])
        else:
            # If no closing --- then treat as no YAML
            self.yaml_eval_default = True
            return

        # Parse the YAML
        try:
            yaml_content = "\n".join(yaml_lines)
            yaml_dict = yaml.safe_load(yaml_content) or {}
        except (yaml.YAMLError, AttributeError):
            # On parse error (i.e., invalid YAML), fall back to default True
            self.yaml_eval_default = True
            return

        # Extract execute.eval setting
        execute_settings = yaml_dict.get("execute", {})
        if isinstance(execute_settings, dict):
            eval_setting = execute_settings.get("eval", True)
            # Convert to boolean (handle string representations)
            if isinstance(eval_setting, str):
                eval_setting = eval_setting.lower() not in [
                    "false",
                    "no",
                    "0",
                ]
            self.yaml_eval_default = bool(eval_setting)
            return
        self.yaml_eval_default = True

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
        # Parse YAML front matter to get default eval setting
        self.parse_yaml_front_matter(qmd_lines)

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
            self.current_chunk_eval = None  # Reset for new chunk
            if self.preserve_line_count:
                self.py_lines.append("# %% [python]")

        # Check if it is the end of a code chunk
        elif line.strip() == "```":
            self.in_python = False
            self.in_chunk_options = False
            self.current_chunk_eval = None  # Reset after chunk ends
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
        """
        # After the first code line, append all lines unchanged
        if not self.in_chunk_options:
            self._handle_body_line(line)
            return

        # Blank lines within chunk options are kept as-is
        if line.strip() == "":
            self.py_lines.append(line)
            return

        # Remove blank space at start of line
        stripped = line.lstrip()

        # If line is a quarto chunk option...
        if stripped.startswith("#| "):
            self._handle_chunk_option(line, stripped)
        # If line is a comment...
        elif stripped.startswith("#"):
            self._handle_comment_in_options(line)
        # First real code line after options/blanks/comments
        else:
            self._handle_first_code_line(line, stripped)

    def _handle_body_line(self, line: str) -> None:
        """
        Handle a line in the body of a Python chunk (after chunk options).

        Parameters
        ----------
        line : str
            The line to process.
        """
        # Skip lines in chunks where eval is false
        if not self.should_lint_current_chunk():
            self._append_placeholder()
            return
        # Handle quarto include syntax and code annotations, then append as-is
        line = self._handle_includes(line)
        line = self._handle_annotations(line)
        self.py_lines.append(line)

    def _handle_chunk_option(self, line: str, stripped: str) -> None:
        """
        Handle a Quarto chunk option line (starting with `#|`).

        Parameters
        ----------
        line : str
            The original line to process.
        stripped : str
            The line with leading whitespace removed.
        """
        # Parse and store eval option if present in this line
        self.parse_chunk_eval_option(stripped)

        # Don't append if not preserving line count
        if not self.preserve_line_count:
            return

        # Suppress E265 (as will warn for "#|" comment spacing)
        if self.uses_noqa:
            line = self._add_noqa(line, ["E265"])

        self.py_lines.append(line)

    def _handle_comment_in_options(self, line: str) -> None:
        """
        Handle a comment line encountered while still in chunk options.

        Parameters
        ----------
        line : str
            The comment line to process.
        """
        # If chunk should be linted, keep comment (but handle annotations)
        # If eval is false, just append placeholder
        if self.should_lint_current_chunk():
            line = self._handle_annotations(line)
            self.py_lines.append(line)
        else:
            self._append_placeholder()

    def _handle_first_code_line(self, line: str, stripped: str) -> None:
        """
        Handle the first real code line after chunk options, blanks, and
        comments.

        Parameters
        ----------
        line : str
            The original line to process.
        stripped : str
            The line with leading whitespace removed.
        """
        # Skip lines in chunks where eval is false
        if not self.should_lint_current_chunk():
            self._append_placeholder()
            self.in_chunk_options = False
            return

        # Handle quarto include syntax and code annotations
        line = self._handle_includes(line)
        line = self._handle_annotations(line)

        # Add noqa suppressions for spacing warnings at chunk boundaries
        if self.uses_noqa:
            line = self._add_noqa_for_first_code_line(line, stripped)

        self.py_lines.append(line)
        self.in_chunk_options = False

    def _append_placeholder(self) -> None:
        """
        Append a placeholder comment line (`# -`) if preserving line count.
        """
        if self.preserve_line_count:
            self.py_lines.append("# -")

    def _add_noqa_for_first_code_line(self, line: str, stripped: str) -> str:
        """
        Add appropriate noqa suppressions for the first code line in a chunk.

        Always suppresses E305 (expected 2 blank lines after top-level
        statement). Also suppresses E302 if the line starts a function, class,
        or decorator.

        Parameters
        ----------
        line : str
            The line to add noqa comments to.
        stripped : str
            The line with leading whitespace removed.

        Returns
        -------
        str
            The line with appropriate noqa suppressions appended.
        """
        # Check for @ too as can have decorators - note, decorators are only
        # applied to functions or classes
        is_function_or_class = (
            stripped.startswith("@")
            or stripped.startswith("def")
            or stripped.startswith("class")
        )
        # Suppress E302 (expected 2 blank lines) in addition to E305
        if is_function_or_class:
            return self._add_noqa(line, ["E302", "E305"])
        return self._add_noqa(line, ["E305"])

    def should_lint_current_chunk(self) -> bool:
        """
        Determine if the current chunk should be linted.

        Returns
        -------
        bool
            True if chunk should be linted (eval is True), False otherwise.
        """
        # Chunk-level setting overrides YAML default
        if self.current_chunk_eval is not None:
            return self.current_chunk_eval
        return self.yaml_eval_default

    def parse_chunk_eval_option(self, stripped: str) -> None:
        """
        Parse chunk options to extract eval setting.

        Searches for lines like "#| eval: false" or "#| eval: true"
        within chunk options.

        Parameters
        ----------
        stripped : str
            The line to parse (with blank space at start removed).

        Returns
        -------
        None
            Stores the eval setting in self.current_chunk_eval attribute.
            Sets to True for "true"/"yes"/"1", False for "false"/"no"/"0",
            Does not modify self.current_chunk_eval if no eval option found.
        """
        # Extract the part after "#| "
        options_part = stripped[3:]

        # Look for eval: pattern
        eval_match = re.search(
            r"eval\s*:\s*(['\"]?)(\w+)\1", options_part
        )

        if eval_match:
            value = eval_match.group(2).lower()
            if value in ["true", "yes", "1"]:
                self.current_chunk_eval = True
            elif value in ["false", "no", "0"]:
                self.current_chunk_eval = False
            else:
                self.current_chunk_eval = None

        # If no eval match found, do NOT modify self.current_chunk_eval
        # This preserves any previously parsed eval setting from earlier lines

    def _add_noqa(self, line: str, suppress: List[str]) -> str:
        """
        Add noqa suppressions to a line for specified error codes.

        If the line is within the allowed max line length, E501 (line too long)
        is also suppressed, since the added noqa comment may push it over the
        limit.

        Parameters
        ----------
        line : str
            The line of code.
        suppress : List[str]
            The error code(s) to suppress (e.g. ["E302"]).

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
        Remove in-line quarto code annotations (and any whitespace prior).

        These include:
        - `#<<` used by shafayetShafee's line-highlight extension.
        - `# <n>` used by Quarto code annotations (e.g., `# <1>`).

        Parameters
        ----------
        line : str
            The line to process.

        Returns
        -------
        str
            The line with trailing whitespace and any "#<<" at the end removed.
        """
        # Strip "#<<" annotations
        line = re.sub(r"\s*#<<\s*$", "", line)
        # Strip Quarto code annotations like "# <1>"
        line = re.sub(r"\s*# <\d+>\s*$", "", line)
        return line


def get_unique_filename(path: Union[str, Path]) -> Path:
    """
    Generate a unique file path by appending "_n" before the file extension
    if needed.

    If the given path already exists, this function appends an incrementing
    number before the file extension (e.g., "file_1.py") until an unused
    filename is found.

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
    PosixPath('script_1.py')  # if 'script.py' exists
    """
    path = Path(path)
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    n = 1
    while True:
        new_name = f"{stem}_{n}{suffix}"
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
