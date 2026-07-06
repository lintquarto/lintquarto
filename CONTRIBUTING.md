# Contributing

Thank you for your interest in contributing! Contributions are very welcome. 😊

<br>

## Bug reports and feature requests

Before opening an issue, please search [existing issues](https://github.com/lintquarto/lintquarto/issues/) to avoid duplicates. If an issue exists, you can add a comment with additional details and/or upvote (👍) the issue. If there is not an existing issue, please open one and provide as much detail as possible.

**For feature requests or documentation improvements**, please describe your suggestion clearly.

**For bugs**, include:
  * Steps to reproduce.
  * Expected and actual behaviour.
  * Environment details (operating system, python version, dependencies).
  * Relevant files (e.g. problematic `.qmd` files).

<br>

## Code contributions

1. Fork the repository.

2. Create a new branch for your feature or fix.

3. Make your changes and commit them with clear, descriptive messages using the [conventional commits standard](https://www.conventionalcommits.org/en/v1.0.0/).

4. Open a pull request against our repository. Describe your changes and reference any related issues.

<br>

## Development environment

If you want to contribute to `lintquarto` or run its tests, you'll need some additional tools. These are declared in `pyproject.toml` as:

* The `all` extra under `[project.optional-dependencies]` (all possible linters and code checkers).
* The `dev` dependency group under `[dependency-groups]` (packaging, docs, tests, etc.).

Set up a Python environment using your preferred tool (e.g., `conda`, `uv`, etc.) then activate it. For example, to work with conda:

```{.bash}
conda create -n lintquarto python=3.12
conda activate lintquarto
```

From the project root, install the package in editable mode with all supported code quality tools:

```{.bash}
pip install -e ".[all]"
```

Then install the development dependencies declared in `pyproject.toml`:

```{.bash}
pip install --group dev
```

Confirm the required packages are installed:

```{.bash}
pip list
```

> **Note:** On 10 February 2026, found incompatible `quartodoc` and `griffe`, so had to lock `griffe` at 1.14.0.

### Quarto

Quarto (used for the docs) is a standalone tool - install it from <https://quarto.org/docs/get-started/>.

<br>

## Tests

Run all tests (with coverage):

```{.bash}
pytest --cov
```

Run an individual test file:

```{.bash}
pytest tests/test_back.py
```

Run a specific test:

```{.bash}
pytest tests/test_linters.py::test_supported_error
```

<br>

## Style

This project uses [Ruff](https://docs.astral.sh/ruff/) and lintquarto for linting and formatting checks.

Ruff configuration, including exclusions and per-file ignores, is defined in `pyproject.toml`. To run:

```bash
ruff format
ruff check --fix
```

We follow the [numpydoc](https://numpydoc.readthedocs.io/en/latest/format.html) style for docstrings.

### Pre-commit

Install pre-commit hooks:

```bash
pre-commit install
```

**Not running in the right environment?** You may find the pre-commit fails if it is using the wrong environment - I've found this to be the case in VSCode. I've found the simplest way to fix this is to work on the command line, activate the environment, and then either do the commit directly there (i.e., `git add`, `git commit`) or launch VS Code (`code .`) which ensures it inherits the environment.

**Unstaged files detected** If you see `[WARNING] Unstaged files detected` during commit, this is normal; pre-commit is just temporarily saving your unstaged changes. The real blocker is any "linting failed" message or linter error output that follows—fix those errors in the listed files, re-stage, and commit again! *This message can occur when there are linting issues in your staged files when trying to commit, but you also have some unstaged files present. With no unstaged files present, message will be like `Git: Lint Package...... failed`*.

<br>

## Documentation

Build and preview the documentation locally:

```{.bash}
make -C docs
```

When running this, function documentation will be automatically generated from the codebase using `quartodoc`

<br>

## Supported python versions

`lintquarto` supports only actively maintained Python versions. Python 3.7 is end-of-life and Python 3.8 is in security-fix-only mode.

Historically, the package targeted Python 3.7+ because the codebase depended on features introduced in Python 3.5-3.7 (e.g., `subprocess.run()`, f-strings, and `text=True` in `subprocess.run()`). We have since dropped 3.7 and 3.8 to align with current practice.

This follows [NEP 29 guidance](https://numpy.org/neps/nep-0029-deprecation_policy.html) used across the scientific Python ecosystem and keeps our tooling, packaging, and test matrix manageable.

Python 3.9 support is not possible, as this package uses the tree-sitter-markdown package which requires Python 3.10+ and above.

<br>

## Updating the package

### Preparation

Before proceeding, you will need to have cloned the `lintquarto/staged-recipes` repository which is used to push updates to conda.

```{.bash}
git clone https://github.com/lintquarto/staged-recipes
```

### Workflow for updates

If you are a maintainer and need to publish a new release:

1. Update the `CHANGELOG.md`.

2. Update the version number in `__init__.py`, `CITATION.cff` and `README.md` citation, and update the date in `CITATION.cff`.

3. Create a release on GitHub. This will automatically:

* Archive to Zenodo.
* Build and publish the package on PyPI (via `build-publish.yaml`).
* Update the conda build recipe in `amyheather/lintquarto-feedstock` and create a pull request to merge into the conda-forge feedstock.

4. Open and merge the pull request.

**Token requirements:** This action assumes we have a `FEEDSTOCK_PR_TOKEN` in our secrets. If this expires or is not present, we can recreate it as follows:

* Amy Heather - go to Settings → Developer settings → Personal access tokens → Tokens (classic). Generate a new class token. For scope, tick: ✅ repo.
* Copy the token, and update the `FEEDSTOCK_PR_TOKEN` secret in `lintquarto/lintquarto` settings with the new value.
* Re-run the workflow.

<br>

## Code of conduct

Please be respectful and considerate. See the [code of conduct](https://github.com/lintquarto/lintquarto/blob/main/CODE_OF_CONDUCT.md) for details.

<br>

## Contributors

If your name or contributions are missing from the README, or if you contributed in ways not captured by the current role emojis, please create an issue and use:

```
@all-contributors please add @githubuser for ...
```

Then list appropriate contribution types from [allcontributors.org/docs/en/emoji-key](https://allcontributors.org/docs/en/emoji-key) (e.g., code, review, doc, content, bug, ideas, infra).

Alternatively, you can update it from the command line. This may be preferable, as the bot will create GitHub issues that email people when they are added.

You'll need to install the [All-Contributors CLI tool](https://allcontributors.org/cli/installation/):

```
npm i -D all-contributors-cli
```

You can then run the following and select/enter relevant information when prompted:

```
npx all-contributors
```

If you want to remove specific contributions or people, edit the `.all-contributorsrc` file then run the following to regenerate the table in `README.md`. (Don't edit `README.md`, as it is just generated based on `.all-contributorsrc`).

```
npx all-contributors generate
```

<br>

## Journal of Open Source Software (JOSS)

The `inst/` folder contains materials related to the submission to JOSS.

* `paper.md` - paper
* `paper.bib` - references
* `codemeta.json` - paper metadata generate using <https://gist.github.com/arfon/478b2ed49e11f984d6fb>.

There is also a [GitHub action which renders the paper as a PDF](https://github.com/lintquarto/lintquarto/actions/workflows/draft-pdf.yml).
