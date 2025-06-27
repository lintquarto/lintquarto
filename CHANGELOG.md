# Changelog

All notable changes to this project are documented.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Dates formatted as YYYY-MM-DD as per [ISO standard](https://www.iso.org/iso-8601-date-and-time-format.html).

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