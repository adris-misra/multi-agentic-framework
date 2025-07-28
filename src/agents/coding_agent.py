# src/agents/coding_agent.py

from autogen import ConversableAgent
import openai

class CodingAgent(ConversableAgent):
    """
    Agent that translates structured software requirements into Python code.
    Can also refine the code based on feedback from code reviewers.
    """
    def __init__(self, name):
        super().__init__(name=name)

    def run(self, requirement: dict, feedback: str = None) -> str:
        """
        Generates Python code based on the structured requirement.
        If feedback is provided, it incorporates the suggestions.
        """
        prompt = f"""
        You are a senior Python developer.
        Generate production-quality Python code based on the structured software requirements below.
        
        Requirements:
        {requirement}

        {"Consider this feedback for code revision:\n" + feedback if feedback else ""}

        Output only the complete Python code. Do not include explanations or markdown formatting.
        """
        return self.llm_complete(prompt)

    def llm_complete(self, prompt: str) -> str:
        """
        Calls the OpenAI API to generate code from the given prompt.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a Python coding assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message["content"].strip()
