Usage:

```
lintquarto [-h] [-l LINTER [LINTER ...]] [-p PATHS [PATHS ...]] [-e [[exclude_paths] ...]] [-n] [-v] [-k] {list} ...
```

Lint Python code in Quarto (.qmd) files.

Options:

* `-h, --help` - show this help message and exit
* `-l LINTER [LINTER ...], --linters LINTER [LINTER ...]` - Linters to run. Valid options: ['flake8', 'mypy', 'pycodestyle', 'pydoclint', 'pyflakes', 'pylint', 'pyright', 'pyrefly', 'pytype', 'radon-cc', 'radon- mi', 'radon-raw', 'radon-hal', 'ruff', 'vulture']
* `-p PATHS [PATHS ...], --paths PATHS [PATHS ...]` - Quarto files and/or directories to lint.
* `-e [[exclude_paths] ...], --exclude [[exclude_paths] ...]` - Files and/or directories to exclude from linting.
* `-n, --lint-non-exec` - Also lint non-executable Python code chunks
* `-v, --verbose` - Verbose output.
* `-k, --keep-temp` - Keep temporary .py files after linting.

Commands:

* `list` - List supported linters and whether they are available.

Passing extra arguments directly to linters is not supported.
Only `.qmd` files are processed.