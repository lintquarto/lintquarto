# Contributing

Thank you for your interest in contributing!

<br>

## Workflow for bug reports, feature requests and documentation improvements

Before opening an issue, please search [existing issues](https://github.com/amyheather/pylintqmd/issues/) to avoid duplicates. If there is not an existing issue, please open open and provide as much detail as possible.

* **For feature requests or documentation improvements**, please describe your suggestion clearly.
* **For bugs**, include:
    * Steps to reproduce.
    * Expected and actual behaviour.
    * Environment details (operating system, python version, dependencies).
    * Relevant files (e.g. problematic `.qmd` files).

<br>

## Workflow for code contributions (bug fixes, enhancements)

1. Fork the repository and clone your fork.

2. Create a new branch for your feature or fix:

```
git checkout -b my-feature
```

3. Make your changes and commit them with clear, descriptive messages using the [conventional commits standard](https://www.conventionalcommits.org/en/v1.0.0/).

4. Push your branch to your fork:

```
git push origin my-feature
```

5. Open a pull request against the main branch. Describe your changes and reference any related issues.

<br>

## Development and testing

### Dependencies

If you want to contribute to `pylintqmd` or run its tests, you'll need some additional tools:

* **flit** (for packaging and publishing)
* **pytest** (for running tests)
* **twine** (for uploading to PyPI)
* `-e .` (for an editable install of the package)

These are listed in `requirements.txt` for convenience.

To set up your development environment, run:

```
pip install -r requirements.txt
```

### Tests

To run tests:

```
pytest
```

### Updating the package

If you are a maintainer and need to publish a new release:

1. Update the `CHANGELOG.md`.

2. Update the version number in `__init__.py`, `CITATION.cff` and `README.md` citation.

3. Build and publish using flit or twine.

To upload to PyPI using `flit`:

```
flit publish
```

To upload to PyPI using `twine`: remove any existing builds, then build the package locally and push with twine, entering the API token when prompted:

```
rm -rf dist/
flit build
twine upload --repository pypi dist/*
```

For test runs, you can use the same method with test PyPI:

```
rm -rf dist/
flit build
twine upload --repository testpypi dist/*
```

<br>

## Code of conduct

Please be respectful and considerate. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.