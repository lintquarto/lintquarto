<div align="center">

# lintquarto

| | |
| --- | --- |
| **Project info:** | ![Code licence](https://img.shields.io/badge/Licence-MIT-A6CE39?&labelColor=gray)    [![DOI](https://img.shields.io/badge/DOI-10.5281/zenodo.15731161-A6CE39?&logoColor=white)](https://doi.org/10.5281/zenodo.15731161)    [![ORCID](https://img.shields.io/badge/ORCID_Amy_Heather-0000--0002--6596--3479-A6CE39?&logo=orcid&logoColor=white)](https://orcid.org/0000-0002-6596-3479)    <!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section --> [![All Contributors](https://img.shields.io/badge/all_contributors-8-orange.svg?style=flat-square)](#contributors-) <!-- ALL-CONTRIBUTORS-BADGE:END --> [![pyOpenSci Peer-Reviewed](https://pyopensci.org/badges/peer-reviewed.svg)](https://github.com/pyOpenSci/software-review/issues/257) |
| **Installation:** | [![PyPI](https://img.shields.io/pypi/v/lintquarto?&labelColor=gray)](https://pypi.org/project/lintquarto/)     [![Anaconda-Server Badge](https://anaconda.org/conda-forge/lintquarto/badges/version.svg)](https://anaconda.org/conda-forge/lintquarto) |
| **Metrics:** | [![PyPI downloads](https://static.pepy.tech/badge/lintquarto)](https://pepy.tech/project/lintquarto)    [![PyPI downloads](https://static.pepy.tech/badge/lintquarto/month)](https://pepy.tech/project/lintquarto)    [![PyPI downloads](https://static.pepy.tech/badge/lintquarto/week)](https://pepy.tech/project/lintquarto)    ![Conda Downloads](https://img.shields.io/conda/d/conda-forge/lintquarto)    ![GitHub Repo stars](https://img.shields.io/github/stars/lintquarto/lintquarto)    ![GitHub forks](https://img.shields.io/github/forks/lintquarto/lintquarto)    ![GitHub last commit](https://img.shields.io/github/last-commit/lintquarto/lintquarto)    ![GitHub Release Date](https://img.shields.io/github/release-date/lintquarto/lintquarto) |
| **Build & quality status:** | [![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)    [![codecov](https://codecov.io/gh/lintquarto/lintquarto/graph/badge.svg?token=F58MDYN3J2)](https://codecov.io/gh/lintquarto/lintquarto)    [![Tests](https://github.com/lintquarto/lintquarto/actions/workflows/tests.yaml/badge.svg)](https://github.com/lintquarto/lintquarto/actions/workflows/tests.yaml)    [![Docs](https://github.com/lintquarto/lintquarto/actions/workflows/docs.yaml/badge.svg)](https://github.com/lintquarto/lintquarto/actions/workflows/docs.yaml)    [![Lint](https://github.com/lintquarto/lintquarto/actions/workflows/lint.yaml/badge.svg)](https://github.com/lintquarto/lintquarto/actions/workflows/lint.yaml)    [![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/format.json)](https://github.com/astral-sh/ruff) |
| **Supported platforms:** | ![Python 3.10\|3.11\|3.12\|3.13](https://img.shields.io/badge/Python-3.10%7C3.11%7C3.12%7C3.13-blue)    ![OS](https://img.shields.io/badge/OS-Windows%20%7C%20Linux%20%7C%20macOS-blue?logo=windows&logo=linux&logo=apple) |

</div>

<br>

**Package for running linters, formatters, static type checkers and code analysis tools on python code in quarto (`.qmd`) files.**

By default, python code validation tools can't check embedded python code in Quarto files. This package fills that gap, enabling analysts and researchers to run python quality checks within Quarto documents.

Currently supported:

* Linters: [pylint](https://github.com/pylint-dev/pylint), [flake8](https://github.com/pycqa/flake8), [pydoclint](https://github.com/jsh9/pydoclint), [pyflakes](https://github.com/PyCQA/pyflakes), [ruff](https://github.com/astral-sh/ruff), [vulture](https://github.com/jendrikseipp/vulture), and [pycodestyle](https://github.com/PyCQA/pycodestyle).
* Static type checkers: [basedpyright](https://github.com/DetachHead/basedpyright), [mypy](https://github.com/python/mypy), [pyright](https://github.com/microsoft/pyright), [pyrefly](https://github.com/facebook/pyrefly), and [pytype](https://github.com/google/pytype).
* Code analysis tools: [radon](https://github.com/rubik/radon).
* Formatters (alpha): [ruff](https://github.com/astral-sh/ruff).

[![Click to view docs](https://img.shields.io/badge/🖱️_Click_to_view_package_documentation-37a779?style=for-the-badge)](https://lintquarto.github.io/lintquarto/)

*This package is featured on [awesome-quarto](https://github.com/mcanouil/awesome-quarto).*

*This package has been [reviewed by PyOpenSci](https://github.com/pyOpenSci/software-submission/issues/257).*

<p align="center">
  <img src="https://github.com/lintquarto/lintquarto/raw/main/docs/images/linting.png" alt="Linting illustration" width="400"/>
</p>

<br>

## Installation

You can install **lintquarto** with pip (from [PyPI](https://pypi.org/project/lintquarto/) or [GitHub](https://github.com/lintquarto/lintquarto)) or conda (from [conda-forge](https://anaconda.org/conda-forge/lintquarto)).

### Install with pip

```
pip install lintquarto
```

To include your selection of linters, install them as needed.

For a one-step installation that includes lintquarto and all supported linters and type checkers, use:

```
pip install lintquarto[all]
```

### Install with uv

```
uv add lintquarto
```

Or to include all supported linters and type checkers:

```
uv add "lintquarto[all]"
```

### Install with conda

```
conda install conda-forge::lintquarto
```

With conda, only the main lintquarto tool is installed. If you want to use any linters or type checkers, you must install them separately (either with conda or pip, depending on availability).




### Development version

To install the latest development version of `lintquarto` directly from this repository:

```
pip install git+https://github.com/lintquarto/lintquarto
```

If you also want all supported linters and type checkers in one step, install from a local clone in editable mode with the `all` extra:

```
git clone https://github.com/lintquarto/lintquarto.git
cd lintquarto
pip install -e ".[all]"
```

<br>

## Getting started using `lintquarto`

### Usage

<!-- cli-help:start -->
Usage:

```
lintquarto [-h] [-l LINTER [LINTER ...]] [-f FORMATTER [FORMATTER ...]] [-p PATHS [PATHS ...]] [-e [[exclude_paths] ...]] [-n] [-v] [-k] [-c COMMAND] {list} ...
```

Lint Python code in Quarto (.qmd) files.
Configuration can also be provided in pyproject.toml under [tool.lintquarto].
CLI arguments override configuration file. WARNING: Formatter option currently
in alpha, with known bugs and further testing required. If you run into any
problems, feel free to open a GitHub issue and contribute to code if you'd
like to!

Options:

* `-h, --help` - show this help message and exit
* `-l, --linters LINTER [LINTER ...]` - Linters to run. Valid options: ['basedpyright', 'flake8', 'mypy', 'pycodestyle', 'pydoclint', 'pyflakes', 'pylint', 'pyright', 'pyrefly', 'pytype', 'radon-cc', 'radon-mi', 'radon-raw', 'radon-hal', 'ruff', 'vulture']
* `-f, --formatters FORMATTER [FORMATTER ...]` - Formatter to run. Valid options: ['ruff-format', 'ruff-check-fix'].
* `-p, --paths PATHS [PATHS ...]` - Quarto files and/or directories to lint.
* `-e, --exclude [[exclude_paths] ...]` - Files and/or directories to exclude from linting.
* `-n, --lint-non-exec` - Also lint non-executable Python code chunks
* `-v, --verbose` - Verbose output.
* `-k, --keep-temp` - Keep temporary .py files after linting.
* `-c, --custom-commands COMMAND` - Custom command to run against the generated .py file. Repeat for multiple commands. Example: --custom- commands "mytool"

Commands:

* `list` - List supported linters and whether they are available.

Passing extra arguments directly to linters is not supported.
Only `.qmd` files are processed.
<!-- cli-help:end -->

### Configuration file

As an alternative to passing flags on every run, you can declare your settings once in a `[tool.lintquarto]` section in your `pyproject.toml`. The arguments are eqvuialent to those used on the command line. For example:

```{.toml}
[tool.lintquarto]
linters = [
  "ruff",
  "pycodestyle",
]
paths = [
  "examples/",
  "dashboard/index.qmd",
]
lint-non-exec = false
```

With this in place, you can run `lintquarto` with no arguments.

**Note:** CLI flags will always take priority over `pyproject.toml`. If you supply `-l` or `-p` on the command line, those values are used and the corresponding config file values are ignored. `exclude` and `custom-commands` are additive - values from both sources are merged together.

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
lintquarto -l ruff -p . -e examples ignore
```

```{.bash}
lintquarto -l ruff -p . -e analysis/test.qmd
```

### Find out more

Visit our website to find out more and see examples from running with each code validation tool.

[![Click to view docs](https://img.shields.io/badge/🖱️_Click_to_view_package_documentation-37a779?style=for-the-badge)](https://lintquarto.github.io/lintquarto/)

<br>

## Community

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="25%"><a href="https://www.linkedin.com/in/amyheather"><img src="https://avatars.githubusercontent.com/u/92166537?v=4?s=100" width="100px;" alt="Amy Heather"/><br /><sub><b>Amy Heather</b></sub></a><br /><a href="#design-amyheather" title="Design">🎨</a> <a href="https://github.com/lintquarto/lintquarto/commits?author=amyheather" title="Documentation">📖</a> <a href="#ideas-amyheather" title="Ideas, Planning, & Feedback">🤔</a> <a href="#infra-amyheather" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="#maintenance-amyheather" title="Maintenance">🚧</a> <a href="https://github.com/lintquarto/lintquarto/commits?author=amyheather" title="Tests">⚠️</a> <a href="https://github.com/lintquarto/lintquarto/issues?q=author%3Aamyheather" title="Bug reports">🐛</a> <a href="https://github.com/lintquarto/lintquarto/commits?author=amyheather" title="Code">💻</a></td>
      <td align="center" valign="top" width="25%"><a href="https://github.com/isabelizimm"><img src="https://avatars.githubusercontent.com/u/54685329?v=4?s=100" width="100px;" alt="Isabel Zimmerman"/><br /><sub><b>Isabel Zimmerman</b></sub></a><br /><a href="#ideas-isabelizimm" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/lintquarto/lintquarto/commits?author=isabelizimm" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="25%"><a href="https://github.com/jaycrick"><img src="https://avatars.githubusercontent.com/u/114450568?v=4?s=100" width="100px;" alt="Jacob Cumming"/><br /><sub><b>Jacob Cumming</b></sub></a><br /><a href="https://github.com/lintquarto/lintquarto/issues?q=author%3Ajaycrick" title="Bug reports">🐛</a> <a href="https://github.com/lintquarto/lintquarto/commits?author=jaycrick" title="Documentation">📖</a> <a href="#ideas-jaycrick" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/lintquarto/lintquarto/commits?author=jaycrick" title="Tests">⚠️</a> <a href="https://github.com/lintquarto/lintquarto/commits?author=jaycrick" title="Code">💻</a></td>
      <td align="center" valign="top" width="25%"><a href="https://jon-e.net/"><img src="https://avatars.githubusercontent.com/u/12961499?v=4?s=100" width="100px;" alt="Jonny Saunders"/><br /><sub><b>Jonny Saunders</b></sub></a><br /><a href="https://github.com/lintquarto/lintquarto/issues?q=author%3Asneakers-the-rat" title="Bug reports">🐛</a> <a href="https://github.com/lintquarto/lintquarto/commits?author=sneakers-the-rat" title="Code">💻</a> <a href="#ideas-sneakers-the-rat" title="Ideas, Planning, & Feedback">🤔</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="25%"><a href="https://sammirosser.com/"><img src="https://avatars.githubusercontent.com/u/29951987?v=4?s=100" width="100px;" alt="Sammi Rosser"/><br /><sub><b>Sammi Rosser</b></sub></a><br /><a href="https://github.com/lintquarto/lintquarto/commits?author=Bergam0t" title="Code">💻</a> <a href="https://github.com/lintquarto/lintquarto/commits?author=Bergam0t" title="Documentation">📖</a> <a href="https://github.com/lintquarto/lintquarto/commits?author=Bergam0t" title="Tests">⚠️</a></td>
      <td align="center" valign="top" width="25%"><a href="https://github.com/aselaws"><img src="https://avatars.githubusercontent.com/u/22793789?v=4?s=100" width="100px;" alt="Anna Laws"/><br /><sub><b>Anna Laws</b></sub></a><br /><a href="https://github.com/lintquarto/lintquarto/commits?author=aselaws" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="25%"><a href="https://github.com/nlebovits"><img src="https://avatars.githubusercontent.com/u/111617674?v=4?s=100" width="100px;" alt="Nissim Lebovits"/><br /><sub><b>Nissim Lebovits</b></sub></a><br /><a href="#ideas-nlebovits" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="25%"><a href="https://experts.exeter.ac.uk/19244-thomas-monks"><img src="https://avatars.githubusercontent.com/u/881493?v=4?s=100" width="100px;" alt="Tom Monks"/><br /><sub><b>Tom Monks</b></sub></a><br /><a href="https://github.com/lintquarto/lintquarto/commits?author=TomMonks" title="Documentation">📖</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!

Curious about contributing? Check out the [contributing guidelines](CONTRIBUTING.md) to learn how you can help. Every bit of help counts, and your contribution - no matter how minor - is highly valued.

<br>

## How to cite `lintquarto`

Please cite the repository on GitHub, PyPI, conda and/or Zenodo:

> Heather, A. (2026). lintquarto (v0.13.1).  https://github.com/lintquarto/lintquarto.
>
> Heather, A. (2026). lintquarto (v0.13.1). https://pypi.org/project/lintquarto/.
>
> Heather, A. (2026). lintquarto (v0.13.1). https://anaconda.org/conda-forge/lintquarto.
>
> Heather, A. (2026). lintquarto (v0.13.1). https://doi.org/10.5281/zenodo.15731161.

Citation instructions are also provided in `CITATION.cff`.

<br>

## Acknowledgements

This project was written and maintained by hand, with occasional use of Perplexity AI during development (specific models and versions varied over time).

AI assistance was used for small, targeted tasks (e.g. help when troubleshooting, identifying issues, refining docstrings, improving code structure), rather than to generate complete functions or substantial content.

All code and design decisions were reviewed and finalised by a human. For transparency, the use of AI is acknowledged, but the project should not be considered AI‑generated.
