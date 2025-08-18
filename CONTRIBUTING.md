# Contributing

Thank you for your interest in contributing! 🤗

This file covers:

* 🐞 Workflow for bug reports, feature requests and documentation improvements
* 🚀 Workflow for code contributions (bug fixes, enhancements)
* 🛠️ Development and testing
* 📦 Updating the package
* 🤝 Code of conduct

<br>

## 🐞 Workflow for bug reports, feature requests and documentation improvements

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

## 🚀 Workflow for code contributions (bug fixes, enhancements)

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

## 🛠️ Development and testing

### Dependencies

If you want to contribute to `lintquarto` or run its tests, you'll need some additional tools:

| Tool | Purpose |
| - | - |
| **check-dependencies** | Test for undeclared dependencies |
| **flit** | Packaging and publishing |
| **genbadge** | Create coverage badge (README) |
| **grayskull** | Uploading to `conda-forge` |
| **jupyter** | Run python code in docs |
| **pytest** | Run tests |
| **pytest-cov** | Calculate coverage |
| **twine** | Upload to PyPI |
| **types-toml** | Required by `mypy` |
| **quartodoc** | Generate API docs |
| `-e .[all]` | Editable install + all linters |

These are listed in `requirements-dev.txt` for convenience. To set up your development environment, create an environment (e.g. `virtualenv`) and run:

```{.bash}
pip install -r requirements-dev.txt
```

For testing only (used by GitHub actions):

```{.bash}
pip install -r requirements-test.txt
```

You can also install the packages in `requirements-dev.txt` when you install `lintquarto` by running:

```{.bash}
pip install lintquarto[dev]
```

Quarto (used for the docs) is a standalone tool - install it from https://quarto.org/docs/get-started/.

<br>

### Dependency versions

Contributors are encouraged to install and use the **latest versions** of development tools. This helps keep the project compatible with current tooling and catches issues early.

If you need a fully reproducible and stable setup, use the provided Conda environment file. This file pins all development tool versions, including Python:

```{.bash}
conda env create -f requirements-stable.yml
```

To update the stable environment, run `conda update --all` and test thoroughly (running tests, building documentation), and then update `requirements-stable.yml` with any changes.

<br>

### Docstrings

We follow the [numpydoc](https://numpydoc.readthedocs.io/en/latest/format.html) style for docstrings, and check these using [pydoclint](https://github.com/jsh9/pydoclint).

<br>

### Tests

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

<br>

### Documentation

Build and preview the documentation locally:

```{.bash}
make -C docs
```

When running this, function documentation will be automatically generated from the codebase using `quartodoc`

<br>

## 📦 Updating the package

### Preparation

Before proceeding, you will need to have cloned the `lintquarto/staged-recipes` repository which is used to push updates to conda.

```{.bash}
git clone https://github.com/lintquarto/staged-recipes
```

### Workflow for updates

If you are a maintainer and need to publish a new release:

1. Update the `CHANGELOG.md`.

2. Update the version number in `__init__.py`, `CITATION.cff` and `README.md` citation, and update the date in `CITATION.cff`.

3. Create a release on GitHub, which will automatically archive to Zenodo.

4. Build and publish using flit or twine.

To upload to PyPI using `flit`:

```{.bash}
flit publish
```

To upload to PyPI using `twine`: remove any existing builds, then build the package locally and push with twine, entering the API token when prompted:

```{.bash}
rm -rf dist/
flit build
twine upload --repository pypi dist/*
```

For test runs, you can use the same method with test PyPI:

```{.bash}
rm -rf dist/
flit build
twine upload --repository testpypi dist/*
```

5. If you haven't already, fork the lintquarto feedstock ([conda-forge/lintquarto-feedstock](https://github.com/conda-forge/lintquarto-feedstock)). This fork must be to your personal GitHub account and not an organisation account. Clone it to your local machine.

If you already have a fork, make sure it is up-to-date by running `git pull`.

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
* Reset base? Yes, should show as `base: 0` in `meta.yaml` by default.
* Re-render? Add the command `@conda-forge-admin, please rerender` to the end of the pull request.

9. Wait for the CI actions to run. If all pass, then you can click "Merge pull request".

<br>

## 🤝 Code of conduct

Please be respectful and considerate. See the [code of conduct](https://github.com/lintquarto/lintquarto/blob/main/CODE_OF_CONDUCT.md) for details.