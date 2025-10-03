#!/bin/bash

errors=0

if [ "$#" -eq 0 ]; then
    # If none specified, run on src/ and tests/ .py files (excluding examples)
    set -- $(find src tests -type f -name "*.py" ! -path "*/tests/examples/*")
fi

echo "Running ruff check..."
ruff check "$@"
(( errors += $? ))

echo "Running flake8..."
flake8 "$@" --ignore DOC,W503
(( errors += $? ))

echo "Running pylint..."
pylint "$@"
(( errors += $? ))

echo "Running radon cc..."
radon cc "$@"
(( errors += $? ))

echo "Running vulture..."
vulture "$@" vulture/whitelist.py
(( errors += $? ))

# These are only run on the package (not on tests)
PKG_FILES=()
for f in "$@"; do
    case "$f" in
        src/*) PKG_FILES+=("$f") ;;
    esac
done

if [ ${#PKG_FILES[@]} -gt 0 ]; then
    echo "Running pydoclint..."
    pydoclint "${PKG_FILES[@]}" --allow-init-docstring=True
    (( errors += $? ))

    echo "Running mypy..."
    mypy "${PKG_FILES[@]}"
    (( errors += $? ))
fi

# After all linters, exit nonzero if any failed
if [ "$errors" -ne 0 ]; then
    echo "One or more linting commands failed."
    exit 1
fi