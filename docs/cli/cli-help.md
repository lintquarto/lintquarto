Usage:

```
lintquarto [-h] [-l LINTER [LINTER ...]] [-f FORMATTER [FORMATTER ...]] [-p PATHS [PATHS ...]] [-e [[exclude_paths] ...]] [-n] [-v] [-k] [-c COMMAND] {list} ...
```

Lint Python code in Quarto (.qmd) files.
Configuration can also be provided in pyproject.toml under [tool.lintquarto].
CLI arguments override configuration file. WARNING: Formatter option currently
in alpha, with known bugs and further testing required. If you run into any
problems, feel free to open a GitHub issue and contribute to code if you'd
like to!

Options:

* `-h, --help` - show this help message and exit
* `-l, --linters LINTER [LINTER ...]` - Linters to run. Valid options: ['basedpyright', 'flake8', 'mypy', 'pycodestyle', 'pydoclint', 'pyflakes', 'pylint', 'pyright', 'pyrefly', 'pytype', 'radon-cc', 'radon-mi', 'radon-raw', 'radon-hal', 'ruff', 'vulture']
* `-f, --formatters FORMATTER [FORMATTER ...]` - Formatter to run. Valid options: ['ruff-format', 'ruff-check-fix'].
* `-p, --paths PATHS [PATHS ...]` - Quarto files and/or directories to lint.
* `-e, --exclude [[exclude_paths] ...]` - Files and/or directories to exclude from linting.
* `-n, --lint-non-exec` - Also lint non-executable Python code chunks
* `-v, --verbose` - Verbose output.
* `-k, --keep-temp` - Keep temporary .py files after linting.
* `-c, --custom-commands COMMAND` - Custom command to run against the generated .py file. Repeat for multiple commands. Example: --custom- commands "mytool"

Commands:

* `list` - List supported linters and whether they are available.

Passing extra arguments directly to linters is not supported.
Only `.qmd` files are processed.