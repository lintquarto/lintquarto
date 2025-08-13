"""Testing certain settings do not impact results."""

from pathlib import Path
import re
import subprocess
import tempfile

from lintquarto.converter import QmdToPyConverter
from lintquarto.linters import Linters


def test_radon_hal_preserve_line_effect():
    """Confirm that preserve_line_count does not impact radon-hal output."""

    def run_radon_hal(preserve_line_count):
        """Helper to run radon-hal, overriding preserve_line_count"""
        qmd_lines = [
            "# Title\n",
            "```{python}",
            "variable = 'apple'\n",
            "y = 2\n",
            "```",
            "\n",
            "This is a sentence.\n",
            "```{python}",
            "# This is a comment.\n",
            "a = 254\n",
            "```\n"
        ]
        # Convert file manually (so can control preservation True/False)
        conv = QmdToPyConverter(linter="radon-hal")
        conv.preserve_line_count = preserve_line_count
        py_file = conv.convert(qmd_lines)

        # Save as tempfile so can use in subprocess.run()
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write("\n".join(py_file).encode("utf-8"))

        # Run radon-hal command (not lintquarto)
        linters = Linters()
        command = linters.supported["radon-hal"] + [str(tmp_path)]
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, check=False
        )
        # Confirm that the preserve_lint_count was as expected and that
        # full output was produced (not blank - checking over 100)
        assert conv.preserve_line_count == preserve_line_count
        assert len(result.stdout) > 100
        # Return the output from radon-hal
        return result.stdout.strip()

    def normalise_radon_output(output: str) -> str:
        """Remove strings from radon output, keeping numeric results."""
        return re.sub(r'^.*:', '<FILE>:', output, flags=re.MULTILINE)

    result_false = normalise_radon_output(run_radon_hal(False))
    result_true = normalise_radon_output(run_radon_hal(True))
    assert result_false == result_true
