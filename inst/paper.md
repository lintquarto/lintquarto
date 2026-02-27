---
title: 'lintquarto: a package for running linters, static type checkers and code analysis tools on Python code in Quarto Markdown files'
tags:
  - Python
  - Quarto
  - lint
authors:
  - name: Amy Heather
    orcid: 0000-0002-6596-3479
    equal-contrib: true
    affiliation: "1"
affiliations:
 - name: University of Exeter, England
   index: 1
date: 20 January 2026
bibliography: paper.bib
---

# Summary

`lintquarto` enables researchers to apply Python linters, static type checkers, and code analysis tools to Python code embedded within Quarto Markdown (`.qmd`) files. Quarto [@allaire_quarto_2022] has become widely adopted in research for creating websites, papers, reports, and documentation that integrate code, narrative, and outputs However, standard Python code quality tools cannot natively run on Quarto Markdown files. `lintquarto` bridges this gap, enabling researchers to maintain Python code quality standards in their Quarto documents.

# Statement of need

Researchers can embed executable Python code in Quarto documents using two formats: Jupyter notebooks (`.ipynb`) or Quarto Markdown. Quarto Markdown is the standard Quarto format. It integrates better with version control because code and text are stored as plain text, and outputs are generated separately during rendering, not stored in the source file. In contrast, `.ipynb` stores outputs and metadata in JSON, making diffs harder to read.

Python researchers using Quarto Markdown face a critical gap: code quality tools cannot natively run on Quarto Markdown files. Code quality tools include:

* Linters - identify style violations and potential bug.
* Static type checkers - verify type annotations.
* Code analysis tools - detect dead code or measure complexity.

These tools are essential for maintaining high code standards and ensuring research code is understandable, maintainable, and reliable.

# State of the field

For Jupyter notebooks, `nbqa` is the etablished solution, wrapping Python linters and formatters so they can run on `.ipynb` files [@nbqa_contributors_nbqa_2025].

For R, the `lintr` packages supports code quality checking across Quarto Markdown, R Markdown and plain R files [@hester_static_2025].

However, researchers preferring Quarto Markdown have no equivalent Python tool.

# Software design

The command-line interface for `lintquarto` accepts three primary arguments: the code quality tools to run, the paths to include, and paths to exclude.

The core workflow converts each Quarto Markdown file into a temporary Python file. Where relevant, the converter preserves line numbers, enabling error messages to map directly back to the original Quarto file. The converter handles Quarto-specific syntax including Quarto chunk options, include directives, in-line annotations (e.g., `#<<`, `# <1>`) and false positives triggered by chunk boundaries.

After conversion, `lintquarto` runs the selected code quality tool on the temporary Python file, captures its output, and rewrites reported paths to reference the original The core workflow converts each Quarto Markdown file into a temporary Python file. Where relevant, the converter preserves line numbers, enabling error messages to map directly back to the original Quarto file. The converter handles Quarto-specific syntax including Quarto chunk options, include directives, in-line annotations (e.g., `#<<`) and false positives triggered by chunk boundaries. 

This approach enables seamless integration. with no modifications to the underlying existing code quality tools, and makes it easy to extend to incorporate new tools. As of publication, the package supports all major Python code quality tools:

* `flake8` [@python_code_quality_authority_flake8_2025]
* `pycodestyle` [@python_code_quality_authority_pycodestyle_2025]
* `pydoclint` [@pydoclint_contributors_pydoclint_2025]
* `pyflakes` [@python_code_quality_authority_pyflakes_2025]
* `pylint` [@pylint_contributors_pylint_2026]
* `ruff` [@astral_ruff_2026]
* `vulture` [@vulture_contributors_vulture_2026]
* `mypy` [@python_mypy_2026]
* `pyrefly` [@facebook_pyrefly_2026]
* `pyright` [@microsoft_pyright_2026]
* `pytype` [@google_pytype_2025]
* `radon` [@radon_contributors_radon_2024]

`lintquarto` is distributed via PyPI and conda-forge, and has minimal dependencies - at present, just `toml` and whichever code quality tools users choose to install. It covers all currently maintained major Python versions. The software has undergone external peer review by PyOpenSci ([issue 257 in their software review repository](https://github.com/pyOpenSci/software-submission/issues/257)), providing additional assurance regarding code quality, documentation, and maintainability.

# Research impact statement

By enabling Python code quality checking in Quarto Markdown, `lintquarto` supports reproducible and reliable scientific research. It has already been adopted in several applied projects in which the author is actively involved, including the DES RAP Book, a step‑by‑step guide for building discrete‑event simulation models in Python and R as part of a reproducible analytical pipeline, where it is used to maintain the quality of code within the Quarto book website [@heather_rap_2026]. It is also used in `lintquarto`'s own documentation site.

# AI usage disclosure

This project was written and maintained by hand, with occasional use of Perplexity AI during development (specific models and versions varied over time).

AI assistance was used for small, targeted tasks in the code (e.g. help when troubleshooting, identifying issues, refining docstrings, improving code structure) and paper (e.g., suggesting improvements for grammar or clarity), rather than to generate complete functions or substantial content.

All code and design decisions were reviewed and finalised by a human.

# References