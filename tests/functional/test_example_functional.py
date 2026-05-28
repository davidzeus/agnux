"""Example functional tests for the Agnux system."""
import pytest


@pytest.mark.functional
class TestExampleFunctional:
    """Functional test cases for example features."""

    def test_example_case_1(self, test_config, setup_teardown):
        """Test example case 1."""
        assert test_config["timeout"] == 30
        print(f"Base URL: {test_config['base_url']}")

    def test_example_case_2(self):
        """Test example case 2."""
        expected = "agnux"
        actual = "agnux"
        assert actual == expected, f"Expected {expected}, got {actual}"

    @pytest.mark.smoke
    def test_smoke_test(self):
        """Smoke test to verify basic functionality."""
        result = 2 + 2
        assert result == 4

    @pytest.mark.slow
    def test_slow_operation(self):
        """Test for slow running operations."""
        import time
        time.sleep(1)  # Simulate slow operation
        assert True


@pytest.mark.functional
def test_simple_functional():
    """Simple functional test without class."""
    data = {"name": "agnux", "version": "1.0"}
    assert data["name"] == "agnux"
    assert "version" in data
