# Contributing

Thank you for your interest in contributing!

This file covers:

* Workflow for bug reports, feature requests and documentation improvements
* Workflow for code contributions (bug fixes, enhancements)
* Development and testing
* Updating the package
* Code of conduct

<br>

## Workflow for bug reports, feature requests and documentation improvements

Before opening an issue, please search [existing issues](https://github.com/lintquarto/lintquarto/issues/) to avoid duplicates. If an issue exists, you can add a comment with additional details and/or upvote (👍) the issue. If there is not an existing issue, please open one and provide as much detail as possible.

* **For feature requests or documentation improvements**, please describe your suggestion clearly.
* **For bugs**, include:
    * Steps to reproduce.
    * Expected and actual behaviour.
    * Environment details (operating system, python version, dependencies).
    * Relevant files (e.g. problematic `.qmd` files).

### Handling bug reports (for maintainers):

* Confirm reproducibility by following the reported steps.
* Label the issue appropriately (e.g. `bug`).
* Request additional information if necessary.
* Link related issues or pull requests.
* Once resolved, close the issue with a brief summary of the fix.

<br>

## Workflow for code contributions (bug fixes, enhancements)

1. Fork the repository and clone your fork.

2. Create a new branch for your feature or fix:

```{.bash}
git checkout -b my-feature
```

3. Make your changes and commit them with clear, descriptive messages using the [conventional commits standard](https://www.conventionalcommits.org/en/v1.0.0/).

4. Push your branch to your fork:

```{.bash}
git push origin my-feature
```

5. Open a pull request against the main branch. Describe your changes and reference any related issues.

<br>

## Development and testing

### Dependencies

If you want to contribute to `lintquarto` or run its tests, you'll need some additional tools. These are declared in `pyproject.toml` as:

* The `all` extra under `[project.optional-dependencies]` (all possible linters and code checkers).
* The `dev` dependency group under `[dependency-groups]` (packaging, docs, tests, etc.).

Key tools include:

| Tool | Purpose |
| - | - |
| **check-dependencies** | Test for undeclared dependencies |
| **genbadge** | Create coverage badge (README) |
| **grayskull** | Uploading to `conda-forge` |
| **jupyter** | Run python code in docs |
| **pre-commit** | To make pre-commit hook that lints files |
| **pytest** | Run tests |
| **pytest-cov** | Calculate coverage |
| **twine** | Upload to PyPI |
| **types-PyYAML** and **types-toml** | Required by `mypy` |
| **quartodoc** | Generate API docs |
| `-e .[all]` | Editable install + all linters |

<br>

### Setting up a dev environment with uv

We recommend using **uv** for dependency management. You should follow instructions from uv documentation for installing it onto your operating system.

#### 1. Start with the recorded environment

In the project root:

```{.bash}
uv sync --all-extras
```

This will use the Python version recorded in `.python-version` and installs the dependency versions recorded in `uv.lock`.

It will install the dev dependency group by default, but you need to add the command `--all-extras` to instruct it to also install the `[project.optional-dependencies].all` packages.

Run the test suite to confirm everything passes:

```{.bash}
uv run pytest
```

To see the installed packages and versions:

```{.bash}
uv run pip list
```

#### 2. Keeping tools up to date (recommended)

It's helpful if contributors periodically bump to the latest compatible versions, so we keep a latest stable, reproducible setup checked into version control.

To do that:

```{.bash}
# Optionally bump the Python version used for development
uv python pin 3.12   # or 3.13, etc.

# Upgrade dependencies within the limits of pyproject.toml
uv lock --upgrade

# Recreate the environment with the updated lockfile
uv sync --all-extras

# Re‑run tests and checks
uv run pytest
```

If everything passes, commit the updated `uv.lock` (and `.python-version` if changed) and mention in your pull request that you've refreshed the dev environment to current versions.

> **Note:** On 10 February 2026, found incompatible `quartodoc` and `griffe`, so had to lock `griffe` at 1.14.0 by running:
>
> ```
> uv lock --upgrade-package "griffe==1.14.0"
> uv lock --upgrade-package "griffecli==2.0.0"
> uv lock --upgrade-package "griffelib==2.0.0"
> uv sync
> ```
<br>

### Test-only environment

The GitHub Actions test workflow uses a minimal environment with only test requirements:

```{.bash}
pip install -r requirements-test.txt
```

<br>

### Quarto

Quarto (used for the docs) is a standalone tool - install it from https://quarto.org/docs/get-started/.

<br>

### Docstrings

We follow the [numpydoc](https://numpydoc.readthedocs.io/en/latest/format.html) style for docstrings, and check these using [pydoclint](https://github.com/jsh9/pydoclint).

<br>

### Tests

Run all tests (with coverage):

```{.bash}
uv run pytest --cov
```

Run an individual test file:

```{.bash}
uv run pytest tests/test_back.py
```

Run a specific test:

```{.bash}
uv run pytest tests/test_linters.py::test_supported_error
```

<br>

### Linting

Make scripts executable (first time only):

```{.bash}
chmod +x lint_package.sh
chmod +x lint_docs.sh
```

Lint the package:

```{.bash}
lint_package.sh
```

Lint the documentation:

```{.bash}
lint_docs.sh
```

There is a pre-commit hook provided which will lint the package and documentation with every commit. To make it executable, run:

```{.bash}
uv run pre-commit install
```

**Not running in the right environment?** You may find the pre-commit fails if it is using the wrong environment - I've found this to be the case in VSCode. I've found the simplest way to fix this is to work on the command line, activate the environment, and then either do the commit directly there (i.e., `git add`, `git commit`) or launch VS Code (`code .`) which ensures it inherits the environment.

**Unstaged files detected** If you see `[WARNING] Unstaged files detected` during commit, this is normal; pre-commit is just temporarily saving your unstaged changes. The real blocker is any "linting failed" message or linter error output that follows—fix those errors in the listed files, re-stage, and commit again! *This message can occur when there are linting issues in your staged files when trying to commit, but you also have some unstaged files present. With no unstaged files present, message will be like `Git: Lint Package...... failed`*.

<br>

### Documentation

Build and preview the documentation locally:

```{.bash}
uv run make -C docs
```

When running this, function documentation will be automatically generated from the codebase using `quartodoc`

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

> If you chose to remove `build-publish.yaml`, you could upload to PyPI manually as follows...
> First, remove any existing builds:
>
> ```{.bash}
> rm -rf dist/
> ```
>
> Then build the package locally with `uv`. It will create an isolated build environment, installing `flit_core` (as specified in `pyproject.toml` `[build-system]`).
>
> ```{.bash}
> uv build
> ```
>
> Finally, push with twine, entering the API token when prompted:
>
> ```{.bash}
> twine upload --repository pypi dist/*
> ```
>
> For test runs, you can use the same method with test PyPI:
>
> ```{.bash}
> twine upload --repository testpypi dist/*
> ```

5. If you haven't already, fork the lintquarto feedstock ([conda-forge/lintquarto-feedstock](https://github.com/conda-forge/lintquarto-feedstock)). This fork must be to your personal GitHub account and not an organisation account. Clone it to your local machine.

If you already have a fork, make sure it is up-to-date:

* With the `conda-forge` feedstock - on your forked `main` branch, click "🔄 Sync fork".
* Locally on your `main` branch (`git checkout main`), run `git pull`.

6. Create and checkout a branch - e.g. `update_0_5_0`.

```{.bash}
git checkout -b update_0_5_0
```

7. Use `grayskull` to update the recipe (`recipe/meta.yaml`). It will pull the metadata about the package from PyPI, and will not use your local installation of the package.

```{.bash}
grayskull pypi lintquarto
```

It will create `lintquarto/meta.yaml`. You will need to copy over the contents into `recipe/meta.yaml`. When you do so, make sure to keep the two fixes made to the `meta.yaml` file which are...

Fix A: The addition of a `home` element within `about`.

```{.bash}
home: https://lintquarto.github.io/lintquarto/
```

Fix B: Correct python version requirements syntax as per the [conda-forge documentation](https://conda-forge.org/docs/maintainer/knowledge_base/#noarch-python), using `python_min` for `host` (fixed version), `run` (minimum version) and `requires` (fixed version).

**Note:** Don't need to set the `python_min` anywhere unless it differs from conda default (currently 3.7).

```{.bash}
  host:
    - python {{ python_min }}

...

  run:
    - python >={{ python_min }}

...

  requires:
    - python {{ python_min }}

```

7. Create a commit with the updated feedstock - for example:

```{.bash}
git add --all
git commit -m "updated feedstock to version 0.5.0"
git push
```

8. Use the GitHub website to open a pull request. Completed the provided checklist -

* Personal account? Yes, if you used your GitHub and not an organisation.
* Bump? Not relevant as doing a version update, can remove.
* Reset base? Yes, should show as `number: 0` in `meta.yaml` by default.
* Re-render? Add the command `@conda-forge-admin, please rerender` to the end of the pull request.

9. Wait for the CI actions to run. If all pass, then you can click "Merge pull request".

<br>

## Code of conduct

Please be respectful and considerate. See the [code of conduct](https://github.com/lintquarto/lintquarto/blob/main/CODE_OF_CONDUCT.md) for details.

<br>

## Journal of Open Source Software (JOSS)

The `inst/` folder contains materials related to the submission to JOSS.

* `paper.md` - paper
* `paper.bib` - references
* `codemeta.json` - paper metadata generate using https://gist.github.com/arfon/478b2ed49e11f984d6fb.

There is also a [GitHub action which renders the paper as a PDF](https://github.com/lintquarto/lintquarto/actions/workflows/draft-pdf.yml).