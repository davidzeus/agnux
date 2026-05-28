"""Example integration tests for the Agnux system."""
import pytest


@pytest.mark.integration
class TestIntegrationExample:
    """Integration test cases for multiple components."""

    def test_component_interaction(self, test_config):
        """Test interaction between components."""
        # Example: Test that components work together
        component_a_result = {"status": "ready", "data": []}
        component_b_result = {"status": "ready", "data": []}

        assert component_a_result["status"] == "ready"
        assert component_b_result["status"] == "ready"

    def test_end_to_end_flow(self):
        """Test complete end-to-end flow."""
        # Step 1: Initialize
        state = {"initialized": True}
        assert state["initialized"]

        # Step 2: Process
        state["processed"] = True
        assert state["processed"]

        # Step 3: Validate
        assert state["initialized"] and state["processed"]
