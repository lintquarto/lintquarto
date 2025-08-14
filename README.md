<div align="center">

# lintquarto

![Code licence](https://img.shields.io/badge/🛡️_Code_licence-MIT-8a00c2?&labelColor=gray)
[![ORCID](https://img.shields.io/badge/ORCID_Amy_Heather-0000--0002--6596--3479-A6CE39?&logo=orcid&logoColor=white)](https://orcid.org/0000-0002-6596-3479)
[![PyPI](https://img.shields.io/pypi/v/lintquarto?&labelColor=gray)](https://pypi.org/project/lintquarto/)
[![DOI](https://img.shields.io/badge/DOI-10.5281/zenodo.15731161-486CAC?&logoColor=white)](https://doi.org/10.5281/zenodo.15731161)
[![Coverage](https://github.com/lintquarto/lintquarto/raw/main/images/coverage-badge.svg)](https://github.com/lintquarto/lintquarto/actions/workflows/tests.yaml)
</div>

<br>

**Package for running linters and static type checkers on quarto `.qmd` files.**

Currently supported linters: [pylint](https://github.com/pylint-dev/pylint), [flake8](https://github.com/pycqa/flake8), [pyflakes](https://github.com/PyCQA/pyflakes), [ruff](https://github.com/astral-sh/ruff), [vulture](https://github.com/jendrikseipp/vulture), [radon](https://github.com/rubik/radon), and [pycodestyle](https://github.com/PyCQA/pycodestyle).

It also supports some static type checkers: [mypy](https://github.com/python/mypy), [pyright](https://github.com/microsoft/pyright), [pyrefly](https://github.com/facebook/pyrefly), and [pytype](https://github.com/google/pytype).

[![Code licence](https://img.shields.io/badge/🖱️_Click_to_view_package_documentation-37a779?style=for-the-badge)](https://lintquarto.github.io/lintquarto/)

<p align="center">
  <img src="https://github.com/lintquarto/lintquarto/raw/main/docs/images/linting.png" alt="Linting illustration" width="400"/>
</p>

<br>

## Installation

You can install `lintquarto` from [PyPI](https://pypi.org/project/lintquarto/):

```
pip install lintquarto
```

To also install all supported linters:

```
pip install lintquarto[all]
```

<br>

## Getting started using `lintquarto`

### Usage

**lintquarto -l LINTER [LINTER ...] -p PATH [PATH ...] [-e EXCLUDE [EXCLUDE ...]] [-k]**

* **-l --linters** LINTER [LINTER ...] - Linters to run. Valid options: `pylint`, `flake8`, `pyflakes`, `ruff`, `vulture`, `radon`, `pycodestyle`, `mypy`, `pyright`, `pyrefly`, or `pytype`.
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

<br>

## Community

Curious about contributing? Check out the [contributing guidelines](CONTRIBUTING.md) to learn how you can help. Every bit of help counts, and your contribution - no matter how minor - is highly valued.

<br>

## How to cite `lintquarto`

Please cite the repository on GitHub, PyPI and/or Zenodo:

> Heather, A. (2025). lintquarto (v0.4.0).  https://github.com/lintquarto/lintquarto.
>
> Heather, A. (2025). lintquarto (v0.4.0). https://pypi.org/project/lintquarto/
>
> Heather, A. (2025). lintquarto (v0.4.0). https://doi.org/10.5281/zenodo.15731161.

Citation instructions are also provided in `CITATION.cff`.

<br>

## Acknowledgements

Parts of this package were generated or adapted from code provided by [Perplexity](https://www.perplexity.ai/).