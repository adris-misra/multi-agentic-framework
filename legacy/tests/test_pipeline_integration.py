from unittest.mock import MagicMock, patch
from src.agents.coding_agent import CodingAgent


def test_pipeline_output_format():
    structured_req = {
        "goal": "Add two numbers",
        "features": ["addition"],
        "inputs": ["num1", "num2"],
        "outputs": ["sum"],
    }

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "def add(num1, num2):\n    return num1 + num2"

    with patch("src.agents.coding_agent.openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        agent = CodingAgent("test")
        code = agent.run(structured_req)

    assert isinstance(code, str)
    assert "def" in code
    assert "return" in code
