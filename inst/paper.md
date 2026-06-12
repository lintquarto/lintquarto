---
title: 'lintquarto: a package for running linters, formatters, static type checkers and code analysis tools on Python code in Quarto Markdown files'
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
date: 12 June 2026
bibliography: paper.bib
---

# Summary

`lintquarto` enables researchers to apply Python linters, formatters, static type checkers, and code analysis tools to Python code embedded within Quarto Markdown (`.qmd`) files. Quarto [@allaire_quarto_2022] has become widely adopted in research for creating websites, papers, reports, and documentation that integrate code, narrative, and outputs. However, standard Python code quality tools cannot natively run on Quarto Markdown files. `lintquarto` bridges this gap, enabling researchers to maintain Python code quality standards in their Quarto documents.

# Statement of need

Researchers can embed Python code in Quarto documents using two formats: Jupyter notebooks (`.ipynb`) or Quarto Markdown. Quarto Markdown is the recommended approach. It integrates better with version control because code and text are stored as plain text, and outputs are generated separately during rendering, not stored in the source file. In contrast, `.ipynb` stores outputs and metadata in JSON, making diffs harder to read.

Despite these advantages, Python researchers using Quarto Markdown face a key limitation: code quality tools cannot natively run on Quarto Markdown files. Code quality tools include:

* Linters: Identify style violations and potential bugs.
* Formatters: Automatically format code to address style issues.
* Static type checkers: Verify type annotations.
* Code analysis tools: Detect dead code or measure complexity.

These tools are essential for maintaining high code standards and ensuring research code is understandable, maintainable, and reliable.

# State of the field

For Jupyter notebooks, `nbqa` is the established solution, wrapping Python linters and formatters so they can run on `.ipynb` files [@nbqa_contributors_nbqa_2025].

For R, the `lintr` package supports code quality checking across Quarto Markdown, R Markdown and plain R files [@hester_static_2025].

However, no equivalent Python tool exists for researchers using Quarto Markdown files.

# Software design

The command-line interface for `lintquarto` accepts three primary arguments: the code quality tools to run, the paths to include, and paths to exclude.

The core workflow converts each Quarto Markdown file into a temporary Python file. Where relevant, line numbers are preserved so that error messages map directly back to the original Quarto source. The converter handles Quarto-specific syntax including Quarto chunk options, include directives, in-line annotations (e.g., `#<<`, `# <1>`) and false positives triggered by chunk boundaries.

After conversion, `lintquarto` runs the selected code quality tool on the temporary Python file, captures its output, and rewrites reported paths to reference the original Quarto document. For formatters, `lintquarto` can apply changes back to the source `.qmd` file.

This approach enables seamless integration, with no modifications to the underlying existing code quality tools, and makes it easy to extend to incorporate new tools. As of publication, the package supports all major Python code quality tools:

* `flake8` [@python_code_quality_authority_flake8_2025]
* `pycodestyle` [@python_code_quality_authority_pycodestyle_2025]
* `pydoclint` [@pydoclint_contributors_pydoclint_2025]
* `pyflakes` [@python_code_quality_authority_pyflakes_2025]
* `pylint` [@pylint_contributors_pylint_2026]
* `ruff` [@astral_ruff_2026]
* `mypy` [@python_mypy_2026]
* `pyrefly` [@facebook_pyrefly_2026]
* `pyright` [@microsoft_pyright_2026]
* `basedpyright` [@basedpyright_contributors_basedpyright_2026]
* `pytype` [@google_pytype_2025]
* `vulture` [@vulture_contributors_vulture_2026]
* `radon` [@radon_contributors_radon_2024]

`lintquarto` is distributed via PyPI and conda-forge, and has minimal dependencies. The software has undergone external peer review by PyOpenSci ([issue 257 in their software review repository](https://github.com/pyOpenSci/software-submission/issues/257)), providing additional assurance regarding code quality, documentation, and maintainability.

# Research impact statement

By enabling Python code quality checking in Quarto Markdown, `lintquarto` supports reproducible and reliable scientific research. Early community engagement has included external users submitting feature requests and bug reports, demonstrating clear demand for improved tooling in this space. The project is also recognised in the *Awesome Quarto* repository [@canouil_awesome_2026].

`lintquarto` is already being used in a range of projects. One example from the author's work is the DES RAP Book, a step‑by‑step guide for building discrete‑event simulation models in Python and R as part of a reproducible analytical pipeline, where it is used to maintain the quality of code within the Quarto book website [@heather_rap_2026].

# AI usage disclosure

This project was written and maintained by hand, with occasional use of Perplexity AI during development (specific models and versions varied over time).

AI assistance was used for small, targeted tasks in the code (e.g. help when troubleshooting, identifying issues, refining docstrings, improving code structure) and paper (e.g., suggesting improvements for grammar or clarity), rather than to generate complete functions or substantial content.

All code and design decisions were reviewed and finalised by a human.

# References
