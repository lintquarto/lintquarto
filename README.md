<div align="center">

# lintquarto

**Project info:** 
![Code licence](https://img.shields.io/badge/Licence-MIT-A6CE39?&labelColor=gray)
[![DOI](https://img.shields.io/badge/DOI-10.5281/zenodo.15731161-A6CE39?&logoColor=white)](https://doi.org/10.5281/zenodo.15731161)
[![ORCID](https://img.shields.io/badge/ORCID_Amy_Heather-0000--0002--6596--3479-A6CE39?&logo=orcid&logoColor=white)](https://orcid.org/0000-0002-6596-3479)

**Installation:**
[![PyPI](https://img.shields.io/pypi/v/lintquarto?&labelColor=gray)](https://pypi.org/project/lintquarto/)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/lintquarto/badges/version.svg)](https://anaconda.org/conda-forge/lintquarto)

**Metrics:**
[![PyPI downloads](https://static.pepy.tech/badge/lintquarto)](https://pepy.tech/project/lintquarto)
[![PyPI downloads](https://static.pepy.tech/badge/lintquarto/month)](https://pepy.tech/project/lintquarto)
[![PyPI downloads](https://static.pepy.tech/badge/lintquarto/week)](https://pepy.tech/project/lintquarto)
![Conda Downloads](https://img.shields.io/conda/d/conda-forge/lintquarto)
![GitHub Repo stars](https://img.shields.io/github/stars/lintquarto/lintquarto)
![GitHub forks](https://img.shields.io/github/forks/lintquarto/lintquarto)
![GitHub last commit](https://img.shields.io/github/last-commit/lintquarto/lintquarto)
![GitHub Release Date](https://img.shields.io/github/release-date/lintquarto/lintquarto)


**Build & quality status:**
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![Coverage](https://github.com/lintquarto/lintquarto/raw/main/images/coverage-badge.svg)](https://github.com/lintquarto/lintquarto/actions/workflows/tests.yaml)
[![Tests](https://github.com/lintquarto/lintquarto/actions/workflows/tests.yaml/badge.svg)](https://github.com/lintquarto/lintquarto/actions/workflows/tests.yaml)
[![Docs](https://github.com/lintquarto/lintquarto/actions/workflows/docs.yaml/badge.svg)](https://github.com/lintquarto/lintquarto/actions/workflows/docs.yaml)
[![Lint](https://github.com/lintquarto/lintquarto/actions/workflows/lint.yaml/badge.svg)](https://github.com/lintquarto/lintquarto/actions/workflows/lint.yaml)

**Supported platforms:**
![Python 3.7|3.8|3.9|3.10|3.11|3.12|3.13](https://img.shields.io/badge/Python-3.7%7C3.8%7C3.9%7C3.10%7C3.11%7C3.12%7C3.13-blue)
![OS](https://img.shields.io/badge/OS-Windows%20%7C%20Linux%20%7C%20macOS-blue?logo=windows&logo=linux&logo=apple)

</div>

<br>

**Package for running linters, static type checkers and code analysis tools on python code in quarto (`.qmd`) files.**

By default, python code validation tools can't check embedded python code in Quarto files. This package fills that gap, enabling analysts and researchers to run python quality checks within Quarto documents.

Currently supported:

* Linters: [pylint](https://github.com/pylint-dev/pylint), [flake8](https://github.com/pycqa/flake8), [pydoclint](https://github.com/jsh9/pydoclint), [pyflakes](https://github.com/PyCQA/pyflakes), [ruff](https://github.com/astral-sh/ruff), [vulture](https://github.com/jendrikseipp/vulture), and [pycodestyle](https://github.com/PyCQA/pycodestyle).
* Static type checkers: [mypy](https://github.com/python/mypy), [pyright](https://github.com/microsoft/pyright), [pyrefly](https://github.com/facebook/pyrefly), and [pytype](https://github.com/google/pytype).
* Code analysis tools: [radon](https://github.com/rubik/radon).

[![Click to view docs](https://img.shields.io/badge/🖱️_Click_to_view_package_documentation-37a779?style=for-the-badge)](https://lintquarto.github.io/lintquarto/)

<p align="center">
  <img src="https://github.com/lintquarto/lintquarto/raw/main/docs/images/linting.png" alt="Linting illustration" width="400"/>
</p>

<br>

## Installation

You can install **lintquarto** with pip ([from PyPI](https://pypi.org/project/lintquarto/)) or conda ([from conda-forge](https://anaconda.org/conda-forge/lintquarto)).

### Install with pip

```
pip install lintquarto
```

To include your selection of linters, install them as needed.

For a one-step installation that includes lintquarto and all supported linters and type checkers, use:

```
pip install lintquarto[all]
```

### Install with conda

```
conda install conda-forge::lintquarto
```

With conda, only the main lintquarto tool is installed. If you want to use any linters or type checkers, you must install them separately (either with conda or pip, depending on availability).

<br>

## Getting started using `lintquarto`

### Usage

**lintquarto -l LINTER [LINTER ...] -p PATH [PATH ...] [-e EXCLUDE [EXCLUDE ...]] [-k]**

* **-l --linters** LINTER [LINTER ...] - Linters to run.
* **-p --paths** PATH [PATH ...]- Quarto files and/or directories to lint.
* **-e --exclude** EXCLUDE [EXCLUDE ...] - Files and/or directories to exclude from linting.
* **-k, --keep-temp** - Keep the temporary `.py` files created during linting (for debugging).

Passing extra arguments directly to linters is not supported. Only `.qmd` files are processed.

### Examples

The linter used is interchangeable in these examples.

Lint all `.qmd` files in the current directory (using `pylint`):

```{.bash}
lintquarto -l pylint -p .
```

Lint several specific files (using `pylint` and `flake8`):

```{.bash}
lintquarto -l pylint flake8 -p file1.qmd file2.qmd
```

Keep temporary `.py` files after linting (with `pylint`)

```{.bash}
lintquarto -l pylint -p . -k
```

Lint all files in current directory (using `ruff`):

* Excluding folders `examples/` and `ignore/`, or-
* Excluding a specific file `analysis/test.qmd`.

```{.bash}
lintquarto -l ruff -p . -e examples,ignore
```

```{.bash}
lintquarto -l ruff -p . -e analysis/test.qmd
```

### Find out more

Visit our website to find out more and see examples from running with each code validation tool.

[![Click to view docs](https://img.shields.io/badge/🖱️_Click_to_view_package_documentation-37a779?style=for-the-badge)](https://lintquarto.github.io/lintquarto/)

<br>

## Community

Curious about contributing? Check out the [contributing guidelines](CONTRIBUTING.md) to learn how you can help. Every bit of help counts, and your contribution - no matter how minor - is highly valued.

<br>

## How to cite `lintquarto`

Please cite the repository on GitHub, PyPI, conda and/or Zenodo:

> Heather, A. (2025). lintquarto (v0.5.0).  https://github.com/lintquarto/lintquarto.
>
> Heather, A. (2025). lintquarto (v0.5.0). https://pypi.org/project/lintquarto/.
>
> Heather, A. (2025). lintquarto (v0.5.0). https://anaconda.org/conda-forge/lintquarto.
>
> Heather, A. (2025). lintquarto (v0.5.0). https://doi.org/10.5281/zenodo.15731161.

Citation instructions are also provided in `CITATION.cff`.

<br>

## Acknowledgements

This project was written and maintained by hand, with occasional use of [Perplexity](https://www.perplexity.ai/) during development. AI assistance was used for small, targeted tasks (e.g. help when troubleshooting, identifying issues, refining docstrings, improving code structure), rather than to generate complete functions or substantial content. All code and design decisions were reviewed and finalised by a human. For transparency, the use of AI is acknowledged, but the project should not be considered AI‑generated.