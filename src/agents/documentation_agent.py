# src/agents/documentation_agent.py

from autogen import ConversableAgent
import openai

class DocumentationAgent(ConversableAgent):
    """
    Agent that generates structured documentation for Python code.
    Covers descriptions, parameters, return values, and usage examples.
    """
    def __init__(self, name):
        super().__init__(name=name)

    def run(self, code: str) -> str:
        """
        Produces well-structured documentation for the given Python code.
        Includes overview, function/class docstrings, and usage examples.
        """
        prompt = f"""
        You are a technical writer.

        Generate complete documentation for the following Python code.
        Include:
        - High-level overview
        - Function and class descriptions
        - Parameters and return types
        - At least one usage example

        Format output as Markdown.

        Code:
        {code}
        """
        return self.llm_complete(prompt)

    def llm_complete(self, prompt: str) -> str:
        """
        Calls the OpenAI API to generate documentation for the code.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a technical documentation specialist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message["content"].strip()
