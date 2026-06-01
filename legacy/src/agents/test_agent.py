# src/agents/test_agent.py

import openai
from src.agents.base_agent import BaseAgent


class TestAgent(BaseAgent):
    """
    Agent that generates test cases for Python code using the pytest framework.
    Includes both unit and integration tests where applicable.
    """

    def __init__(self, name):
        super().__init__(name=name)

    def run(self, code: str) -> str:
        """
        Generates test cases for the given code.
        Each function should have at least one unit test.
        Include one integration test if functions interact.
        """
        prompt = f"""
        You are a QA automation engineer.

        Write test cases for the following Python code using the pytest framework.
        Requirements:
        - At least one unit test per function
        - One integration test if multiple components interact
        - Ensure the code is testable and structured properly
        - Output should only include test code (no explanations)

        Code:
        {code}
        """
        return self.llm_complete(prompt)

    def llm_complete(self, prompt: str) -> str:
        """
        Calls the OpenAI API to generate test code.
        """
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a software test engineer."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
