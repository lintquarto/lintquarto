#!/bin/bash

# Unique set of linters to run (each checking different things)
LINTERS=("ruff check" "pylint" "vulture" "radon cc")

# List of directories to check
DIRS=("src" "tests")

for linter in "${LINTERS[@]}"; do
    echo "Running $linter..."
    for dir in "${DIRS[@]}"; do
        $linter "$dir"
    done
done