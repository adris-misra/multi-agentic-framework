# src/agents/ui_agent.py

from autogen import ConversableAgent
import openai

class UIAgent(ConversableAgent):
    """
    Agent that generates a basic Streamlit UI for interacting with the multi-agent system.
    The UI allows users to input natural language requirements and displays system outputs.
    """
    def __init__(self, name):
        super().__init__(name=name)

    def run(self, code: str) -> str:
        """
        Produces a Streamlit app that collects requirements and displays outputs.
        The backend pipeline is assumed to be triggered externally.
        """
        prompt = f"""
        You are a frontend developer using Streamlit.

        Create a basic Streamlit UI that includes:
        - A text input area for natural language requirements
        - A submit button to simulate sending input to the agent pipeline
        - Placeholder sections to display:
            - Generated Python Code
            - Documentation
            - Test Cases
            - Deployment Script

        Do not include any backend integration logic. Just the frontend layout.

        Reference Code:
        {code}
        """
        return self.llm_complete(prompt)

    def llm_complete(self, prompt: str) -> str:
        """
        Calls the OpenAI API to generate the Streamlit UI script.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a Streamlit UI developer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message["content"].strip()
