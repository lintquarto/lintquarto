#!/bin/bash

echo "Running ruff check..."
ruff check src tests

echo "Running flake8..."
flake8 src tests

echo "Running pylint..."
pylint src tests

echo "Running radon cc..."
radon cc src tests

echo "Running vulture..."
vulture src tests vulture/whitelist.py