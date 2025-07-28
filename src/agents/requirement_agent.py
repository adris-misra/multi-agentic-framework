# src/agents/requirement_agent.py

from autogen import ConversableAgent
import openai

class RequirementAgent(ConversableAgent):
    """
    Agent that converts raw natural language input into a structured software requirement.
    Expected output is a dictionary with keys: goal, features, constraints, inputs, outputs.
    """
    def __init__(self, name):
        super().__init__(name=name)

    def run(self, input_text: str) -> dict:
        """
        Accepts natural language and returns a structured requirements dictionary.
        """
        prompt = f"""
        You are a software business analyst.
        Convert the following user requirement into a structured Python dictionary with keys:
        - goal: (overall purpose)
        - features: (list of key features)
        - constraints: (any system or user constraints)
        - inputs: (user inputs)
        - outputs: (system outputs)

        Input: {input_text}
        """
        response = self.llm_complete(prompt)
        return self._parse_output(response)

    def _parse_output(self, text: str) -> dict:
        """
        Safely evaluate or parse the LLM output into a dictionary.
        """
        try:
            # Assume LLM output is Python-dict-like
            structured_output = eval(text.strip(), {"__builtins__": None}, {})
            if isinstance(structured_output, dict):
                return structured_output
        except Exception:
            pass
        # Fallback if LLM output is invalid
        return {
            "goal": "Unknown",
            "features": [],
            "constraints": [],
            "inputs": [],
            "outputs": []
        }

    def llm_complete(self, prompt: str) -> str:
        """
        Calls the OpenAI API to complete the given prompt using GPT-4.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a requirements analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message["content"]
