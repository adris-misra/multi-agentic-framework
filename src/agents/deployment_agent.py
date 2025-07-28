# src/agents/deployment_agent.py

from autogen import ConversableAgent
import openai

class DeploymentAgent(ConversableAgent):
    """
    Agent that generates a simple deployment script for a Python application.
    Includes setting up a virtual environment, installing dependencies, and running the app.
    """
    def __init__(self, name):
        super().__init__(name=name)

    def run(self, code: str) -> str:
        """
        Generates a bash-based deployment script.
        Assumes the use of virtualenv and pip. Will run main.py after setup.
        """
        prompt = f"""
        You are a DevOps engineer.

        Create a shell script to deploy a Python application based on the following code.
        The script should:
        - Create a virtual environment
        - Install dependencies using pip
        - Run the application using main.py

        Assume dependencies may include: openai, streamlit, pytest

        Code:
        {code}
        """
        return self.llm_complete(prompt)

    def llm_complete(self, prompt: str) -> str:
        """
        Calls the OpenAI API to generate the deployment script.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a DevOps deployment assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message["content"].strip()
