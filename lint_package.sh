#!/bin/bash

echo "Running ruff check..."
ruff check src tests --exclude tests/examples

echo "Running flake8..."
flake8 src tests --exclude tests/examples

echo "Running pylint..."
pylint src tests/*py --ignore=tests/examples

echo "Running radon cc..."
radon cc src tests --exclude tests/examples

echo "Running vulture..."
vulture src tests vulture/whitelist.py --exclude tests/examples