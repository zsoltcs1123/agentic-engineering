---
description: Testing standards and best practices for Python tests
alwaysApply: false
---
# Testing Standards

Follow these principles when writing tests:

## Test Organization

- **Mirror source structure** - Tests should mirror the source code structure
- **Use descriptive test names** - Test names should clearly describe what is being tested
- **One assertion per test** - Each test should verify one behavior (when possible)
- **Use test markers** - Categorize tests with markers (`@pytest.mark.unit`, `@pytest.mark.integration`, etc.)

## Test Structure

- **Arrange-Act-Assert pattern** - Structure tests with clear sections
- **Keep tests focused** - Each test should test one specific behavior
- **Use fixtures for setup** - Share common setup code via pytest fixtures
- **Keep tests independent** - Tests should not depend on each other

## Naming Conventions

- **Test files**: `test_*.py` or `*_test.py`
- **Test functions**: `test_*` prefix
- **Test classes**: `Test*` prefix (if using classes)
- **Descriptive names**: `test_function_name_should_do_something_when_condition`

```python
# Good
def test_get_user_returns_none_when_user_not_found() -> None:
    user = get_user(user_id=999)
    assert user is None

# Bad
def test_get_user() -> None:
    user = get_user(user_id=999)
    assert user is None
```

## Test Markers

Use markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_calculate_total() -> None:
    assert calculate_total([1, 2, 3]) == 6

@pytest.mark.integration
def test_api_create_user() -> None:
    response = create_user_via_api({"name": "Test"})
    assert response.status_code == 201
```

**Available markers**:
- `@pytest.mark.unit` - Fast unit tests (no I/O)
- `@pytest.mark.integration` - Integration tests (require services)
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.api` - API endpoint tests

## Type Hints

Always include type hints in tests:

```python
def test_process_data(data: list[int]) -> None:
    result = process_data(data)
    assert result is not None
```

## Fixtures

Use fixtures for reusable test data and setup:

```python
from dataclasses import dataclass
import pytest

@dataclass
class User:
    id: int
    name: str
    email: str

@pytest.fixture
def sample_user() -> User:
    return User(id=1, name="Test User", email="test@example.com")

def test_user_creation(sample_user: User) -> None:
    assert sample_user.id == 1
    assert sample_user.name == "Test User"
```

## Assertions

- **Use descriptive assertions** - Prefer specific assertions over generic ones
- **Use pytest's assertion introspection** - Let pytest show detailed failure messages
- **Test edge cases** - Include boundary conditions and error cases

```python
# Good - specific assertion
assert user.email == "test@example.com"
assert len(users) == 3
assert "error" in response.text.lower()

# Good - testing edge cases
def test_divide_by_zero_raises_error() -> None:
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)
```

## Mocking and Patching

- **Mock external dependencies** - Don't make real API calls or database queries in unit tests
- **Use `unittest.mock` or `pytest-mock`** - Mock external services
- **Test behavior, not implementation** - Focus on what the code does, not how

```python
from unittest.mock import Mock, patch

def test_send_email_calls_service(mocker: Mock) -> None:
    mock_service = mocker.patch("your_package.email_service.send")
    send_notification("user@example.com", "Hello")
    mock_service.assert_called_once_with("user@example.com", "Hello")
```

## Test Data

- **Use factories or fixtures** - Create test data consistently
- **Keep test data minimal** - Only include what's necessary for the test
- **Use dataclasses** - For structured test data

```python
from dataclasses import dataclass

@dataclass
class TestProduct:
    id: int = 1
    name: str = "Test Product"
    price: float = 10.0

def test_product_creation() -> None:
    product = TestProduct()
    assert product.price == 10.0
```

## Documentation

- **No docstrings** - Test names should be self-explanatory
- **No comments** - Clear test structure makes comments unnecessary
- **Self-documenting code** - Use descriptive variable names and clear assertions

## Best Practices

- **Fast unit tests** - Unit tests should run quickly (no I/O)
- **Isolated tests** - Each test should be independent
- **Repeatable** - Tests should produce the same results every time
- **Test the interface** - Test public APIs, not internal implementation
- **Cover edge cases** - Test boundaries, empty inputs, None values
- **Use parametrize for similar tests** - Avoid duplication

```python
@pytest.mark.parametrize("input_value,expected", [
    (0, 0),
    (1, 1),
    (2, 4),
    (3, 9),
])
def test_square(input_value: int, expected: int) -> None:
    assert square(input_value) == expected
```

## Test Coverage

- **Aim for high coverage** - But focus on meaningful tests
- **Test critical paths** - Prioritize business logic and error handling
- **Don't test implementation details** - Test behavior, not how it's implemented

## Integration Tests

- **Separate from unit tests** - Use markers to distinguish
- **Test real interactions** - Use actual services when appropriate
- **Clean up after tests** - Ensure tests don't leave side effects

```python
@pytest.mark.integration
def test_database_connection() -> None:
    db = connect_to_database()
    assert db.is_connected()
    db.close()
```
