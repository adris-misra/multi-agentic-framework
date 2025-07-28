# src/agents/code_review_agent.py

from autogen import ConversableAgent
import openai

class CodeReviewAgent(ConversableAgent):
    """
    Agent that reviews Python code for correctness, efficiency, security, and readability.
    Returns either 'Approved' or a list of feedback points.
    """
    def __init__(self, name):
        super().__init__(name=name)

    def run(self, code: str) -> str:
        """
        Reviews the provided Python code and returns 'Approved' or suggestions for improvement.
        """
        prompt = f"""
        You are an experienced software reviewer.

        Review the following Python code and evaluate it for:
        - Correctness
        - Efficiency
        - Security
        - Readability and maintainability

        If the code is acceptable as-is, respond with: Approved
        If not, provide detailed suggestions for improvement.

        Code:
        {code}
        """
        return self.llm_complete(prompt)

    def llm_complete(self, prompt: str) -> str:
        """
        Calls the OpenAI API to perform a code review.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a code review expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message["content"].strip()
