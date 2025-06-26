#!/bin/bash

# ----------------------------------------------------------------------------
# Run lintquarto on .qmd files in docs/
# ----------------------------------------------------------------------------

echo "Linting quarto files..."

LINTERS=("ruff check" "pylint" "vulture" "radon cc")

FILES=$(find docs \
    -type f \
    ! -path "docs/pages/api/*" \
    ! -path "docs/pages/tools/examples/*" \
    ! -path "docs/pages/behind_the_scenes/*")

for linter in "${LINTERS[@]}"; do
    echo "Running $linter..."
    lintquarto $linter $FILES
done

# ----------------------------------------------------------------------------
# Run linters on .py files in docs/
# ----------------------------------------------------------------------------

# Find all .py files in docs/, ignoring directories starting with .
PYFILES=$(find docs -type d -name ".*" -prune -false -o -type f -name "*.py" -print)

echo "Running ruff check..."
ruff check $PYFILES

echo "Running pylint..."
pylint $PYFILES

echo "Running radon cc..."
radon cc $PYFILES

echo "Running vulture..."
vulture $PYFILES vulture/whitelist.py