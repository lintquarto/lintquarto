<div align="center">

# lintquarto

![Code licence](https://img.shields.io/badge/🛡️_Code_licence-MIT-8a00c2?style=for-the-badge&labelColor=gray)
[![ORCID](https://img.shields.io/badge/ORCID_Amy_Heather-0000--0002--6596--3479-A6CE39?style=for-the-badge&logo=orcid&logoColor=white)](https://orcid.org/0000-0002-6596-3479)

</div>

<br>

Package for running linters on quarto `.qmd` files.

Currently supported: [pylint](https://github.com/pylint-dev/pylint), [flake8](https://github.com/pycqa/flake8) and [mypy](https://github.com/python/mypy).

<p align="center">
  <img src="images/linting.png" alt="Linting illustration" width="400"/>
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

```{.bash}
lintquarto [linter] [files or folders] [-k | --keep-temp]
```

* **[linter]** - Choose one of the supported linters: `pylint`, `flake8` or `mypy`.
* **[files or folders]** - One or more `.qmd` files or directories to lint.
* **-k, --keep-temp** - Keep the temporary `.py` files created during linting (for debugging).

Only one linter can be specified per command. Passing extra arguments directly to linters is not supported. Only `.qmd` files are processed.

### Examples

The linter used is interchangeable in these examples.

Lint all `.qmd` files in the current directory (using `pylint`):

```{.bash}
lintquarto pylint .
```

Lint a specific file (using `flake8`):

```{.bash}
lintquarto flake8 file.qmd
```

Lint several specific files (using `pylint`):

```{.bash}
lintquarto pylint file1.qmd file2.qmd
```

Lint all `.qmd` files in a folder (using `mypy`):

```{.bash}
lintquarto mypy folder
```

Keep temporary `.py` files after linting (with `pylint`)

```{.bash}
lintquarto pylint . -k
```

<br>

## Community

Curious about contributing? Check out the [contributing guidelines](CONTRIBUTING.md) to learn how you can help. Every bit of help counts, and your contribution - no matter how minor - is highly valued.

<br>

## How to cite `lintquarto`

Please cite the repository on GitHub, PyPI and/or Zenodo:

> Heather, A. (2025). lintquarto (v0.1.0).  https://github.com/lintquarto/lintquarto.
>
> Heather, A. (2025). lintquarto (v0.1.0). https://pypi.org/project/lintquarto/
>
> Heather, A. (2025). lintquarto (v0.1.0). TODO.

Citation instructions are also provided in `CITATION.cff`.

<br>

## Acknowledgements

Parts of this package were generated or adapted from code provided by [Perplexity](https://www.perplexity.ai/).