import pytest

class MockAgent:
    def run(self, input):
        return f"Processed: {input}"

def test_mock_agent_response():
    agent = MockAgent()
    result = agent.run("test input")
    assert result == "Processed: test input"