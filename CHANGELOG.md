# Changelog

All notable changes to this project are documented.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Dates formatted as YYYY-MM-DD as per [ISO standard](https://www.iso.org/iso-8601-date-and-time-format.html).

## v0.6.0 - 2025-09-25

### Added

* **GitHub actions:** Add linting action.
* **Tests:** Add tests relevant to changes/fixes below.

### Changed

* **Acknowledgements:** Redid LLM acknowledgement so just one overarching statement in README, and add more specific details on how it was used, based on PyOpenSci discussions.
* **Converter:** Quarto code chunks now use noqa messages (rather than changing "#| " to "# | ", as they did before).
* **CONTRIBUTING:** Corrected instructions for conda update.
* **process_qmd:** Refactored to reduce complexity and repetition.
* **README:** Add more badges (build & quality status, stars/download metrics) and button linking to documentation.

### Fixed
* **process_qmd:** Replace `...py` in output with just the filename, and not the full file path (as that is there already, depending on linter, so get duplicates).
* **Converter:**
    * "First code line" now excludes comments.
    * Can now handle Quarto {{< include ... >}} syntax (comments the line, else linters break as not valid Python syntax).
    * Can now handle "#<<" code annotations from shafayetShafee's line-highlight extension (removes them and any whitespace prior).
    * Corrected detection of python code chunk start (allowing spaces before {python} and allowing in-line chunk options e.g. {python, echo=...}).
* **GitHub actions:** Linting action now fails even for warning messages (previously, just failed for errors but not warnings).

## v0.5.0 - 2025-08-18

Package now supports `pydoclint`, adds conda-related tooling and optional dev dependencies. Code now uses type hints, and have add some version-specific test and installation skips.

### Added

* **pydoclint:** Add support for a new linter: `pydoclint`.
* **Environment:** Add `grayskull`, `types-toml`, and made a `[dev]` optional dependencies section in `pyproject.toml`. Add exclusions for particular python versions.

### Changed

* **Type hints:** Add type hints to package, and then use `pydoclint` and `mypy` when linting docs and package.
* **CONTRIBUTING:** Improvements include table of contents and instructions for conda upload.
* **Documentation:**
    * Add conda badge and PyPI downloads badges.
    * Add explanation for `mypy` output containing files outside specified path.
    * Mentioned "code analysis tools" (rather than referring to `radon` as a linter).
* **Test:** Utility function for skipping tests when unavailable on certain python versions.

## v0.4.0 - 2025-08-14

Extended support for radon, incorporating commands for maintainability index, Halstead metrics, and raw code metrics. Also some additional tests and documentation improvements, and a few small fixes.

### Added

* **Radon:** Extended support beyond `radon cc` - now also supports `radon mi`, `radon hal` and `radon raw` - which required addition of `preserve_line_count` in `QmdToPyConverter`.
* **Tests:**
    * Add back testing for every linter (`test_back.py`).
    * Add test using `check-dependencies` which tests for missing or undeclared dependencies.
    * Add new tests related to radon changes (`test_preserve_line_count_false_removes_non_code()`, `test_radon_hal_preserve_line_effect()`).
* **Build:** Add `toml` as required dependency

### Changed

* **Radon:** Command for radon cc is now `radon-cc` (was `radon` before).
* **Documentation:**
    * `docs.yaml` now uses Python 3.12 (as one of the linters is unsupported in 3.13).
    * Improved readability of `CONTRIBUTING.md`.
    * Correct statement about only specifying one linter per command in `README.md`.
    * Add back in bold and gap for PyPI button.

### Removed

* **Tests:** Removed some redundant `check_available` tests (which were actually already covered by `check_supported`).

### Fixed

* **File type:** Fixed replacement of `.py` with `.qmd` in the output for some linters.
* **Tests:** Include error in checkd output and remove line numbers for pytype. Add skip for `pytype` back-test for unsupported python versions.
* **`lint_package.sh`:** Only run pylint on files that exist in `tests/` to prevent false error about `tests/__init__.py`.

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