"""Shared pytest fixtures and configurations."""
import pytest
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return {
        "timeout": 30,
        "retries": 3,
        "base_url": os.getenv("TEST_BASE_URL", "http://localhost:8000"),
    }


@pytest.fixture
def setup_teardown():
    """Setup and teardown fixture for tests."""
    # Setup
    print("\n=== Setting up test environment ===")
    yield
    # Teardown
    print("\n=== Tearing down test environment ===")
