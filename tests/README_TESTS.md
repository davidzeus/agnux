# Agnux Functional Tests

## Overview

This directory contains the functional and integration tests for the Agnux system using pytest.

## Structure

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures and configuration
├── README_TESTS.md            # This file
├── functional/
│   ├── __init__.py
│   ├── test_example_functional.py
│   └── test_integration_example.py
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements-test.txt
```

### 2. Configure Environment (Optional)

Create a `.env` file in the project root:

```bash
TEST_BASE_URL=http://localhost:8000
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Functional Tests Only

```bash
pytest -m functional
```

### Run Integration Tests Only

```bash
pytest -m integration
```

### Run Smoke Tests

```bash
pytest -m smoke
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html
```

### Run with Verbose Output

```bash
pytest -v
```

### Run Specific Test File

```bash
pytest tests/functional/test_example_functional.py
```

### Run Specific Test Class

```bash
pytest tests/functional/test_example_functional.py::TestExampleFunctional
```

### Run Specific Test Method

```bash
pytest tests/functional/test_example_functional.py::TestExampleFunctional::test_example_case_1
```

### Run Tests in Parallel

```bash
pytest -n auto
```

### Run with Timeout (30 seconds per test)

```bash
pytest --timeout=30
```

## Test Markers

The following markers are available:

- `@pytest.mark.functional` - Functional tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.smoke` - Smoke tests (quick validation)
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.unit` - Unit tests

## Best Practices

1. **Organize tests by feature**: Group related tests in the same module
2. **Use descriptive names**: Test function names should clearly describe what they test
3. **Use fixtures**: Leverage pytest fixtures for setup/teardown and shared data
4. **Mark tests appropriately**: Use markers to categorize tests
5. **Keep tests independent**: Each test should be independent and not rely on others
6. **Use assertions clearly**: Make assertions explicit and meaningful

## Fixtures

### `test_config`

Provides test configuration:

```python
def test_example(test_config):
    timeout = test_config["timeout"]
    base_url = test_config["base_url"]
```

### `setup_teardown`

Provides setup and teardown hooks:

```python
def test_example(setup_teardown):
    # Setup code runs before this
    pass
    # Teardown code runs after this
```

## Continuous Integration

To run tests in CI/CD pipelines:

```bash
pytest --junitxml=junit.xml --cov=src --cov-report=xml
```

## Troubleshooting

### Tests Not Found

Ensure test files follow the naming convention: `test_*.py`

### Import Errors

Make sure the project is installed in development mode:

```bash
pip install -e .
```

### Fixture Issues

Check that fixtures are defined in `conftest.py` and have the correct scope.
