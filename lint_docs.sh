#!/bin/bash

errors=0

# ----------------------------------------------------------------------------
# Run lintquarto on .qmd files in docs/
# ----------------------------------------------------------------------------

echo "--------------------------------------------------------------------"
echo "Linting quarto files..."
echo "--------------------------------------------------------------------"

LINTERS="ruff flake8 pylint radon-cc vulture pydoclint mypy"
EXCLUDE="docs/pages/api docs/pages/tools/examples"

lintquarto -l $LINTERS -p docs --exclude $EXCLUDE
(( errors += $? ))

# ----------------------------------------------------------------------------
# Run linters on .py files in docs/
# ----------------------------------------------------------------------------

echo "--------------------------------------------------------------------"
echo "Linting python files..."
echo "--------------------------------------------------------------------"

# Find all .py files in docs/, ignoring directories starting with .
PYFILES=$(find docs -type d -name ".*" -prune -false -o -type f -name "*.py" -print)

echo "Running ruff check..."
ruff check $PYFILES
(( errors += $? ))

# Ignore type hint-related warnings (so just arise with pydoclint)
echo "Running flake8..."
flake8 $PYFILES --ignore DOC
(( errors += $? ))

echo "Running pylint..."
pylint $PYFILES
(( errors += $? ))

echo "Running radon cc..."
radon cc $PYFILES
(( errors += $? ))

echo "Running vulture..."
vulture $PYFILES vulture/whitelist.py
(( errors += $? ))

echo "Running pydoclint..."
pydoclint $PYFILES
(( errors += $? ))

echo "Running mypy..."
mypy $PYFILES
(( errors += $? ))

if [ "$errors" -ne 0 ]; then
    echo "One or more linting commands failed."
    exit 1
fi
