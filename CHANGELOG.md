# Changelog

All notable changes to this project are documented.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Dates formatted as YYYY-MM-DD as per [ISO standard](https://www.iso.org/iso-8601-date-and-time-format.html).

## v0.3.0 - 2025-07-07

Major updates include support for multiple linters and file/directory exclusion, expanded testing, several fixes (e.g. false positive linter warnings, deletion of `.py` files, coverage badge), and the removal of `pylama`.

### Added

* **Exclude:** Add an `-e` / `--exclude` flag to exclude files/directories, with examples in documentation.
* **Multiple linters:** Add option to run multiple linters using `-l` / `--linters`.
* **Tests:** Expanded to provide a comprehensive set of unit tests for the `args`, `converter`, `linelength` and `linters` modules, as well as integration and functional tests for the `__main__` module.
* **Test CI:** GitHub actions workflow now runs tests on multiple Python versions (3.7-3.13).

### Changed

* **Converter:** Changed conversion of quarto to python file from a function (`_qmd_lines_to_py_lines`) to a class (`QmdToPyConverter`).
* **Command to run lintquarto:** To run multiple linters, now required to use `-l` / `--linters` for linters and `-p` / `--paths` for files and directories.

### Removed

* **Pre-commit:** Removed, as it was not functioning as intended and a manual workflow is now preferred.
* **`Pylama`:** Removed, since its supported linters are now integrated directly, and the others were either redundant or deprecated [(#25)](https://github.com/lintquarto/lintquarto/issues/25).
* **Behind the scenes:** removed as now more complex and decided better to just look at the code rahter than page in docs, more standard, and up to date, etc.

### Fixed

* **README:** Display of coverage badge.
* **Chunk options:** Amends Quarto code chunk options from `#| ...` to `# | ...` to avoid linting errors.
* **E305:** Linters like `flake8` will warn "Expected 2 blank lines after end of function or class (E305)" at the start of a quarto code cell, but this will *never* be true, so for those linters, `noqa: E305` is always appended.
* **E302:** For functions/classes defined at the start of a quarto code cell, linters like `flake8` will also warn "Expected 2 blank lines, found 0 (E302)". This will also not be true, so in those cases, `noqa: E302` is appended.
* **E501:** When appending `noqa: E302,E305` the line length can then become too long - "Line too long (82 > 79 characters) (E501)". Hence, this warning is disabled in these cases (where the line length was fine before, but not after adding the noqa comment).
* **Deletion of .py file:** When creating the temporary python file, the converter would replace any of the same name in the directory. If not keeping, it would then delete it. This issue has been fixed, by appending the duplicate temporary filename (e.g. `file (1).py`).
* **C0114:** `pylint` will warn "missing-module-docstring / C0114" but this will never be relevant for a quarto file so has been disabled.
* **Errors in `convert_qmd_to_py`:** For `FileNotFoundError` and `PermissionError`, corrected to also `return None` (as already done for `Exception`).
* **Coverage badge:** Coverage badge is now pushed to the repository when generated in the tests GitHub action.

## v0.2.0 - 2025-06-27

Major updates include expanded linter support, new Quarto documentation, and new CI/CD workflows.

### Added

* **Linter support:** Added support for new Python linters: `pyflakes`, `ruff`, `pylama`, `vulture`, `pycodestyle`, `pyright`, `pyrefly` and `pytype`.
* **Documentation:**
    * Introduced Quarto documentation site with getting started, API reference, user guide and detailed linter pages.
    * Add the `downloadthis` extension to allow download buttons in `.qmd` files.
    * Add a Makefile for building and previewing the documentation.
* **CI/CD:** Added GitHub actions to build documentation and run tests.
* **Linting the package:** Added scripts and a pre-commit hook to lint the package code and documentation.
* **Environment:** Created a stable version of the environment with pinned versions using Conda.

### Changed

* **Refactoring:** Refactored and simplified main code and converter logic, and linted the package.
* **README:** Updated with new buttons and shield badges.
* **CONTRIBUTING:** Add instructions on releases, bug reports, dependency versions, testing, and linting.
* **Environment:** Add `jupyter`, `genbadge`, `pre-commit`, `pytest-cov` and `quartodoc` to the environment.

### Fixed

* **README:** Corrected links (PyPI, Zenodo, external images).

## v0.1.0 - 2025-06-24

🌱 First release.

### Added

* Lint Quarto markdown (`.qmd`) files using `pylint`, `flake8`, or `mypy`.