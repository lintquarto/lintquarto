---
title: 'lintquarto: a package for running linters, static type checkers and code analysis tools on python code in quarto markdown files'
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

<!--
Example paper: https://joss.readthedocs.io/en/latest/example_paper.html

(Optional) create a metadata file describing your software and include it in your repository. We provide a script that automates the generation of this metadata: https://gist.github.com/arfon/478b2ed49e11f984d6fb

https://joss.readthedocs.io/en/latest/paper.html
 The paper should be between 750-1750 words. 
-->

# Summary
<!--A description of the high-level functionality and purpose of the software for a diverse, non-specialist audience.-->

`lintquarto` enables existing Python linters, static type checkers, and code analysis tools to run on Python code in Quarto Markdown files. Quarto [@allaire_quarto_2022] has become widely adopted in research for creating websites, papers, reports, and documentation that integrate code, narrative, and outputs However, standard Python code quality tools cannot natively run on Quarto's `.qmd` files. `lintquarto` bridges this gap, allowing researchers to maintain Python code quality standards in their Quarto documents.

# Statement of need
<!-- A section that clearly illustrates the research purpose of the software and places it in the context of related work. This should clearly state what problems the software is designed to solve, who the target audience is, and its relation to other work.-->

Researchers can embed executable Python code in Quarto documents using two formats: Jupyter notebooks (`.ipynb`) or Quarto Markdown (`.qmd`). `.qmd` is the standard Quarto format. It integrates better with version control because code and text are stored as plain text, and outputs are generated separately during rendering, not stored in the source file. In contrast, `.ipynb` stores outputs and metadata in JSON, making diffs harder to read.

Python researchers using Quarto Markdown face a critical gap: code quality tools cannot natively run on `.qmd` files. Code quality tools include linters (which identify style violations and potential bugs), static type checkers (which verify type annotations), and code analysis tools (which detect dead code or measure complexity). These tools are essential for maintaining high code standards and ensuring research code is understandable, maintainable, and reliable.

# State of the field
<!--A description of how this software compares to other commonly-used packages in the research area. If related tools exist, provide a clear “build vs. contribute” justification explaining your unique scholarly contribution and why existing alternatives are insufficient.-->

For Jupyter notebooks, `nbqa` is the stablished solution, wrapping Python linters and formatters so they can run on `.ipynb` files (CITE). However, researchers preferring Quarto Markdown have no equivalent Python tool.

For R, well-established solutions exist: `lintr` supports code quality checking across Quarto Markdown, R Markdown and plain R files (CITE).

`lintquarto` closes this gap by enabling established Python code quality tools to run on Quarto Markdown files.

# Software design
<!--An explanation of the trade-offs you weighed, the design/architecture you chose, and why it matters for your research application. This should demonstrate meaningful design thinking beyond a superficial code structure description.-->

From the command line, users specify which code quality tools to run, which paths to include, and which to exclude. Supported tools at the time of publication are detailed in Table []{label="supported_tools"}. `lintquarto` identifies all relevant `.qmd` files and processes these in turn for each code quality tool.

Each Quarto file is converted into a temporary Python file. The converter walks through the file line-by-line, tracking whether it is inside a Python code chunk or not. For most tools, it preserves line numbers by replacing non-Python lines with placeholder comments so that the temporary `.py` file matches the original `.qmd`.

The converter also handles Quarto-specific syntax. It accounts for chunk options, Quarto include syntax, in-line annotations like `#<<`, and adds `noqa` comments to supress false positives triggered by chunk options or by the way functions and classes appear at chunk boundaries.

`lintquarto` then runs the chosen code quality tool on the temporary Python file, captures its output, and rewrites the reported paths so that messages reference the original Quarto filename.

The design requires no modifications to underlying linters. It has scope to extend to any other relevant tools identified (though at present has tried to cover all popular tools used) as it just runs on py files.

The package is distributed via both PyPI and conda-forge, ensuring accessibility across packaging ecosystems.

The software has been reviewed by PyOpenSci (CITE).

| Category | Tool | Description | Source |
| :-: | :-: | --- | - |
| Linters | `flake8` | Lightweight tool focused on PEP-8 style, basic errors, and code complexity | [@python_code_quality_authority_flake8_2025] |
| Linters | `pycodestyle` | Checks against PEP-8 style guidelines | [@python_code_quality_authority_pycodestyle_2025] |
| Linters | `pydoclint` | Docstring linter | [@pydoclint_contributors_pydoclint_2025] |
| Linters | `pyflakes` | Checks for logical errors like undefined names and unused imports | [@python_code_quality_authority_pyflakes_2025] |
| Linters | `pylint` | Detailed linter that detects errors, bugs, variable naming issues, and other code problems | [@pylint_contributors_pylint_2026] |
| Linters | `ruff` | Modern, ultra-fast linter that implements checks from Flake8 and some other popular plugins | [@astral_ruff_2026] |
| Linters | `vulture` | Finds unused/dead code | [@seipp_jendrikseippvulture_2026] |
| Static type checkers | `mypy` | Python's popular static type checker | [@python_mypy_2026] |
| Static type checkers | `pyrefly` | Meta's Rust-based static type checker (successor to Pyre) | [@facebook_pyrefly_2026] |
| Static type checkers | `pyright` | Microsoft's static type checker | [@microsoft_pyright_2026] |
| Static type checkers | `pytype` | Google's static type checker | [@google_pytype_2025] |
| Code analysis tools | `radon` | calculates complexity, maintainability, raw statistics, and Halstead metrics | [@radon_contributors_radon_2024] |

# Research impact statement
<!--Evidence of realized impact (publications, external use, integrations) or credible near-term significance (benchmarks, reproducible materials, community-readiness signals). The evidence should be compelling and specific, not aspirational.-->

By enabling linting of python code within Quarto Markdown files, this package helps maintain high standards for both code and the data it produces or manipulates, supporting reproducible and reliable scientific research.

`lintquarto` has already been used in existing research projects including the DES RAP Book project (CITE) and sim-tools (CITE). DES RAP Book is educational resource developed by researchers at University of Exeter (me!) teaching how to develop reproducible analytical pipelines in python and r, lintquarto used to maintain code quality. sim-tools is a package, used for package documentation, likewise used for litnquarto documentation itself too.

(I could explain it came out of a need for something liek this on STARS, is why I made it, used it there?)

mention pyopensci again?

# AI usage disclosure

This project was written and maintained by hand, with occasional use of Perplexity AI during development (specific models and versions varied over time).

AI assistance was used for small, targeted tasks in the code (e.g. help when troubleshooting, identifying issues, refining docstrings, improving code structure) and paper (e.g., suggestion improvements for grammar/clarity/conciseness), rather than to generate complete functions or substantial content.

All code and design decisions were reviewed and finalised by a human.

# References