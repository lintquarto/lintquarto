#!/bin/bash

echo "Running ruff check..."
ruff check src tests --exclude tests/examples

echo "Running flake8..."
flake8 src tests --exclude tests/examples --ignore DOC,W503

echo "Running pylint..."
pylint src tests/*py --ignore=tests/examples

echo "Running radon cc..."
radon cc src tests --exclude tests/examples

echo "Running vulture..."
vulture src tests vulture/whitelist.py --exclude tests/examples

# These are only run on the package (not on tests)

echo "Running pydoclint..."
pydoclint src --allow-init-docstring=True

echo "Running mypy..."
mypy src