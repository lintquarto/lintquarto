#!/bin/bash

# ----------------------------------------------------------------------------
# Run lintquarto on .qmd files in docs/
# ----------------------------------------------------------------------------

echo "--------------------------------------------------------------------"
echo "Linting quarto files..."
echo "--------------------------------------------------------------------"

LINTERS="ruff flake8 pylint vulture radon"
EXCLUDE="docs/pages/api docs/pages/tools/examples docs/pages/behind_the_scenes"

lintquarto -l $LINTERS -p docs --exclude $EXCLUDE

# ----------------------------------------------------------------------------
# Run linters on .py files in docs/
# ----------------------------------------------------------------------------

echo "--------------------------------------------------------------------"
echo "Linting python files..."
echo "--------------------------------------------------------------------"

# Find all .py files in docs/, ignoring directories starting with .
PYFILES=$(find docs -type d -name ".*" -prune -false -o -type f -name "*.py" ! -path "*/behind_the_scenes/file.py" -print)

echo "Running ruff check..."
ruff check $PYFILES

# echo "Running flake8..."
flake8 $PYFILES

echo "Running pylint..."
pylint $PYFILES

echo "Running radon cc..."
radon cc $PYFILES

echo "Running vulture..."
vulture $PYFILES vulture/whitelist.py