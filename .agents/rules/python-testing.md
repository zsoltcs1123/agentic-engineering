---
description: Testing standards and best practices for Python tests
alwaysApply: false
---

# Testing Standards

## Test Organization

- **Mirror source structure** - Tests live in `tests/` at the repo root, mirroring the package structure (e.g. `tests/gateflow/unit/`)
- **Test markers** - Categorize every test with a marker:
  - `@pytest.mark.unit` - Fast, no I/O
  - `@pytest.mark.integration` - Requires services or real I/O
  - `@pytest.mark.slow` - Long-running tests
  - `@pytest.mark.api` - API endpoint tests

## Style

- **No docstrings** on tests - Test names should be self-explanatory
- **No comments** - Clear test structure makes comments unnecessary
- **Descriptive names** - `test_<subject>_<expected_behavior>_when_<condition>`
- **Mock external dependencies** - Use `unittest.mock` or `pytest-mock`, never make real API/DB calls in unit tests

## What to Test (and What Not To)

- **Don't test language features** - Do not write tests that verify standard library or language behavior (dataclass defaults, dict construction, import availability, `callable()` checks). Only test logic, constraints, or integrations that _we_ defined. If removing the test wouldn't risk missing a regression in _our_ code, the test shouldn't exist.
- **Test behavior, not implementation** - Focus on what the code does, not how
- **Prioritize constraints and business rules** - Validation logic, edge cases, error handling
- **Use parametrize** to cover boundary values without duplicating test bodies
