#!/bin/bash
# Wrapper script to run pre-commit hooks before Commitizen interactive commit

set -e

echo "Running pre-commit hooks..."
uv run pre-commit run --all-files

if [ $? -eq 0 ]; then
    echo ""
    echo "Pre-commit hooks passed. Starting Commitizen..."
    echo ""
    uv run cz commit "$@"
else
    echo ""
    echo "Pre-commit hooks failed. Please fix the issues before committing."
    exit 1
fi
