from src.agents.coding_agent import CodingAgent

def test_pipeline_output_format():
    # Simulate structured requirement
    structured_req = {
        "goal": "Add two numbers",
        "features": ["addition"],
        "inputs": ["num1", "num2"],
        "outputs": ["sum"]
    }

    agent = CodingAgent("test")
    code = agent.run(structured_req)

    assert isinstance(code, str)
    assert "def" in code
    assert "return" in code