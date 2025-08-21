"""Helper functions for the tools pages in the user guide."""

from typing import Optional


def generate_html(
    pypi_url: str,
    github_url: str,
    conda_url: Optional[str] = None
):
    """
    Generate HTML buttons with icons for PyPI, GitHub, and (optionally) Conda.

    Parameters
    ----------
    pypi_url : str
        The URL to the project's PyPI page.
    github_url : str
        The URL to the project's GitHub repository.
    conda_url : Optional[str]
        The URL to the project's Conda page. If none provided, then will not
        include a conda button.
    """
    html = f"""
<div style="display: flex; gap: 1em; margin-bottom: 1em;">
  <a href="{pypi_url}" target="_blank" style="text-decoration: none;">
    <span style="display: inline-flex; align-items: center; background:
    #3775A9; color: #fff; border-radius: 20px; padding: 0.4em 1em;
    font-weight: 600; gap: 0.5em;">
      <img src=
      "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/pypi.svg"
      alt="PyPI" width="20" height="20" style="filter: brightness(0)
      invert(1);" />
      View on PyPI
    </span>
  </a>
  <a href="{github_url}" target="_blank" style="text-decoration: none;">
    <span style="display: inline-flex; align-items: center; background: #000;
    color: #fff; border-radius: 20px; padding: 0.4em 1em; font-weight: 600;
    gap: 0.5em;">
      <img src=
      "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/github.svg"
      alt="GitHub" width="20" height="20" style="filter: brightness(0)
      invert(1);" />
      View on GitHub
    </span>
  </a>
"""
    if conda_url:
        html += f"""<a href="{conda_url}" target="_blank"
        style="text-decoration: none;">
  <span style="display: inline-flex; align-items: center;
  background: #3EB049; color: #fff; border-radius: 20px; padding: 0.4em 1em;
  font-weight: 600; gap: 0.5em;">
    <img src=
    "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/anaconda.svg"
    alt="Conda" width="20" height="20" style="filter: brightness(0)
    invert(1);" />
    View on Conda
  </span>
</a>
"""
    html += "</div>"
    print(html)


def print_quarto(file_path: str):
    """
    Print quarto file as text with line numbers, without executing any code.

    Parameters
    ----------
    file_path : str
        Path to the quarto .qmd file to print.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        for line_number, line_content in enumerate(file, start=1):
            if line_number < 10:
                print(f"{line_number}:     {line_content}", end="")
            else:
                print(f"{line_number}:    {line_content}", end="")
