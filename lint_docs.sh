#!/bin/bash

errors=0

# ===============================
# Handle arguments for .py/.qmd
# ===============================
if [ "$#" -eq 0 ]; then
    # No args: find all .py and .qmd files under docs/ (excluding some)
    PYFILES=$(find docs -type d -name ".*" -prune -false -o -type f -name "*.py" ! -path "docs/pages/api/*" ! -path "docs/pages/tools/examples/*" -print)
    QMDFILES=$(find docs -type d -name ".*" -prune -false -o -type f -name "*.qmd" ! -path "docs/pages/api/*" ! -path "docs/pages/tools/examples/*" -print)
    # Build new argument list for the whole script
    set -- $PYFILES $QMDFILES
fi

# Split .py and .qmd files (for targeted linters)
PYFILES=()
QMDFILES=()
for f in "$@"; do
    case "$f" in
        *.py) PYFILES+=("$f") ;;
        *.qmd) QMDFILES+=("$f") ;;
    esac
done

# ----------------------------------------------------------------------------
# Run lintquarto on .qmd files in docs/
# ----------------------------------------------------------------------------
if [ ${#QMDFILES[@]} -gt 0 ]; then
    echo "--------------------------------------------------------------------"
    echo "Linting quarto files..."
    echo "--------------------------------------------------------------------"
    LINTERS="ruff flake8 pylint radon-cc vulture pydoclint mypy"
    EXCLUDE="docs/pages/api docs/pages/tools/examples"
    lintquarto -l $LINTERS -p "${QMDFILES[@]}" -e $EXCLUDE
    (( errors += $? ))
fi

# ----------------------------------------------------------------------------
# Run linters on .py files in docs/
# ----------------------------------------------------------------------------
if [ ${#PYFILES[@]} -gt 0 ]; then
    echo "--------------------------------------------------------------------"
    echo "Linting python files..."
    echo "--------------------------------------------------------------------"

    echo "Running ruff check..."
    ruff check "${PYFILES[@]}"
    (( errors += $? ))

    echo "Running flake8..."
    flake8 "${PYFILES[@]}" --ignore DOC
    (( errors += $? ))

    echo "Running pylint..."
    pylint "${PYFILES[@]}"
    (( errors += $? ))

    echo "Running radon cc..."
    radon cc "${PYFILES[@]}"
    (( errors += $? ))

    echo "Running vulture..."
    vulture "${PYFILES[@]}" vulture/whitelist.py
    (( errors += $? ))

    echo "Running pydoclint..."
    pydoclint "${PYFILES[@]}"
    (( errors += $? ))

    echo "Running mypy..."
    mypy "${PYFILES[@]}"
    (( errors += $? ))
fi

if [ "$errors" -ne 0 ]; then
    echo "One or more linting commands failed."
    exit 1
fi
