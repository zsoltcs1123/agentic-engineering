#!/bin/bash
# Run tests with coverage report (terminal only)
uv run pytest --cov=src --cov-report=term-missing "$@"
