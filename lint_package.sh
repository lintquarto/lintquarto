#!/bin/bash

errors=0

echo "Running ruff check..."
ruff check src tests --exclude tests/examples
(( errors += $? ))

echo "Running flake8..."
flake8 src tests --exclude tests/examples --ignore DOC,W503
(( errors += $? ))

echo "Running pylint..."
pylint src tests/*py --ignore=tests/examples
(( errors += $? ))

echo "Running radon cc..."
radon cc src tests --exclude tests/examples
(( errors += $? ))

echo "Running vulture..."
vulture src tests vulture/whitelist.py --exclude tests/examples
(( errors += $? ))

# These are only run on the package (not on tests)

echo "Running pydoclint..."
pydoclint src --allow-init-docstring=True
(( errors += $? ))

echo "Running mypy..."
mypy src
(( errors += $? ))

# After all linters, exit nonzero if any failed
if [ "$errors" -ne 0 ]; then
    echo "One or more linting commands failed."
    exit 1
fi