# multi_agent_framework/main.py

from autogen import ConversableAgent, UserProxyAgent

# Agent imports: Each agent handles a specific stage of the pipeline
from src.agents.requirement_agent import RequirementAgent  # Parses raw input into structured requirements
from src.agents.coding_agent import CodingAgent            # Generates code from structured requirements
from src.agents.code_review_agent import CodeReviewAgent   # Reviews code and provides approval or feedback
from src.agents.documentation_agent import DocumentationAgent  # Documents the code clearly
from src.agents.test_agent import TestAgent                # Generates test cases using pytest
from src.agents.deployment_agent import DeploymentAgent    # Prepares deployment script
from src.agents.ui_agent import UIAgent                    # Creates a Streamlit-based UI stub

def main():
    # Initialize agents
    user_agent = UserProxyAgent(name="User")
    req_agent = RequirementAgent("RequirementAgent")
    code_agent = CodingAgent("CodingAgent")
    review_agent = CodeReviewAgent("CodeReviewAgent")
    doc_agent = DocumentationAgent("DocumentationAgent")
    test_agent = TestAgent("TestAgent")
    deploy_agent = DeploymentAgent("DeploymentAgent")
    ui_agent = UIAgent("UIAgent")

    # Step 1: Requirement Analysis - Convert user input to structured format
    raw_input = input("Please describe your software requirement: ")
    structured_req = req_agent.run(raw_input)

    # Validate structured requirement format to ensure downstream compatibility
    if not isinstance(structured_req, dict) or not structured_req.get("goal"):
        print("Error: Invalid structured requirement format. Please try again.")
        return

    # Step 2: Code Generation - Translate requirements into executable Python code
    code = code_agent.run(structured_req)

    # Step 3: Code Review - Loop until code is approved
    while True:
        feedback = review_agent.run(code)
        if feedback == "Approved":
            break
        code = code_agent.run(structured_req, feedback)

    # Step 4: Documentation - Generate structured doc with explanations and usage
    documentation = doc_agent.run(code)

    # Step 5: Test Case Generation - Produce unit and integration tests
    test_cases = test_agent.run(code)

    # Step 6: Deployment Script - Create setup and run script
    deploy_script = deploy_agent.run(code)

    # Step 7: Streamlit UI Code - Generate a UI to interact with the system
    ui_code = ui_agent.run(code)

    # Output final results for user review
    print("\n=== Final Code ===\n", code)
    print("\n=== Documentation ===\n", documentation)
    print("\n=== Test Cases ===\n", test_cases)
    print("\n=== Deployment Script ===\n", deploy_script)
    print("\n=== Streamlit UI Code ===\n", ui_code)

if __name__ == "__main__":
    main()
