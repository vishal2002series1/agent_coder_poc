from programmer_agent import ProgrammerAgent
from test_designer_agent import TestDesignerAgent
from test_executor_agent import TestExecutorAgent
import os
from dotenv import load_dotenv

import json
import time

class AgentCoderPOC:
    def __init__(self, config):
        self.programmer = ProgrammerAgent(
            api_key=config["api_key"],
            endpoint=config["endpoint"],
            deployment=config["deployment"],
            api_version=config["api_version"]
        )
        self.test_designer = TestDesignerAgent(
            api_key=config["api_key"],
            endpoint=config["endpoint"],
            deployment=config["deployment"],
            api_version=config["api_version"]
        )
        self.test_executor = TestExecutorAgent()
        self.max_iterations = 5
        self.results_log = []

    def generate_and_test_code(self, requirements):
        print(f"🚀 Starting AgentCoder POC for: {requirements[:100]}...")

        # Step 1: Generate test cases
        print("\n📝 Step 1: Generating test cases...")
        test_result = self.test_designer.generate_tests(requirements)
        if not test_result["success"]:
            return {"success": False, "error": "Failed to generate tests", "details": test_result}
        tests = test_result["tests"]
        print(f"✅ Test cases generated successfully")

        # Step 2: Iterative code generation and testing
        feedback = None
        for iteration in range(1, self.max_iterations + 1):
            print(f"\n🔄 Iteration {iteration}: Generating code...")
            code_result = self.programmer.generate_code(requirements, feedback)
            if not code_result["success"]:
                print(f"❌ Code generation failed: {code_result['error']}")
                continue
            code = code_result["code"]
            print(f"✅ Code generated")

            # Execute code with tests
            print(f"🧪 Testing code...")
            execution_result = self.test_executor.execute_with_tests(code, tests)

            # Log this iteration
            iteration_log = {
                "iteration": iteration,
                "code": code,
                "tests": tests,
                "execution_result": execution_result,
                "timestamp": time.time()
            }
            self.results_log.append(iteration_log)

            if execution_result["success"]:
                print(f"🎉 Success! Code passed all tests in iteration {iteration}")
                return {
                    "success": True,
                    "final_code": code,
                    "tests": tests,
                    "iterations": iteration,
                    "execution_result": execution_result,
                    "log": self.results_log
                }
            else:
                error_stage = execution_result.get("stage", "unknown")
                error_type = execution_result.get("error_type", "unknown")
                print(f"❌ {error_stage.title()} failed ({error_type})")
                print(f"📋 Error: {execution_result['error'][:200]}...")
                feedback = execution_result["feedback"]

        print(f"\n💥 Failed to generate working code after {self.max_iterations} iterations")
        return {
            "success": False,
            "error": "Max iterations reached without success",
            "final_code": code if 'code' in locals() else None,
            "tests": tests,
            "iterations": self.max_iterations,
            "last_execution_result": execution_result if 'execution_result' in locals() else None,
            "log": self.results_log
        }

    def save_results(self, results, filename="agentcoder_results.json"):
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"📁 Results saved to {filename}")

    def cleanup(self):
        self.test_executor.cleanup()

def main():
    # Configuration using provided API keys
    load_dotenv()

    # Configuration using environment variables
    config = {
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION")
    }

    agent_coder = AgentCoderPOC(config)
    try:
        requirements = """
        Create a Python function called 'fibonacci_sequence' that:
        1. Takes an integer n as input
        2. Returns a list containing the first n numbers in the Fibonacci sequence
        3. Handle edge cases like n <= 0
        4. Should be efficient for reasonable values of n (up to 100)
        """
        requirements = """
        Create a Python function called 'reverse_string' that:
        1. Takes a string as input.
        2. Returns the reversed string.
        3. Handles edge cases like empty strings and None input.
        """
        requirements = """
        Create a Python function called 'analyze_sentiment' that:
        1. Takes a text string as input.
        2. Analyzes the sentiment of the text (positive, negative, neutral).
        3. Returns a dictionary with 'sentiment' (string) and 'confidence' (float between 0-1).
        4. Handles edge cases like empty strings and None input.
        5. The function should work for basic sentiment analysis.
        """
        requirements = """
        Create a Python function called 'analyze_sentiment' that:
        1. Takes a text string as input.
        2. Uses the TextBlob library to analyze the sentiment of the text (positive, negative, neutral).
        3. Returns a dictionary with 'sentiment' (string) and 'confidence' (float between 0-1).
        4. Handles edge cases like empty strings and None input.
        5. The function should work for basic sentiment analysis.
        
        """
        requirements = """
        Create a Python function called 'analyze_sentiment' that:
        1. Takes a text string as input.
        2. Uses the TextBlob library to analyze the sentiment of the text (positive, negative, neutral).
        3. Returns a dictionary with 'sentiment' (string) and 'confidence' (float between 0-1).
        4. Handles edge cases like empty strings and None input.
        5. The function should work for basic sentiment analysis.
        6. In the test cases, just check if the code is getting executed in the environment without any runtime or import or anyother error.
        """

        requirements = """
        Create a Python function called 'analyze_sentiment' that:
        1. Takes a text string as input.
        2. Uses the TextBlob library to analyze the sentiment of the text (positive, negative, neutral).
        3. Returns a dictionary with 'sentiment' (string) and 'confidence' (float between 0-1).
        4. Handles edge cases like empty strings and None input.
        5. The function should work for basic sentiment analysis.
        6. In the test cases, DO NOT check for specific output values. Only check that the function runs without raising any exceptions (such as ImportError, RuntimeError, or AssertionError). For each test, simply call the function and ensure no error is raised.
        7. Example test: try: analyze_sentiment("I love programming!"); except Exception as e: assert False, f"Function raised an exception: {e}"
        """
        
        results = agent_coder.generate_and_test_code(requirements)
        agent_coder.save_results(results)
        if results["success"]:
            print(f"\n🎯 SUCCESS SUMMARY:")
            print(f"   ✅ Iterations needed: {results['iterations']}")
            print(f"   📝 Final code length: {len(results['final_code'])} characters")
            print(f"   🧪 All tests passed!")
        else:
            print(f"\n❌ FAILURE SUMMARY:")
            print(f"   💥 Failed after {results['iterations']} iterations")
            print(f"   📋 Last error: {results.get('last_execution_result', {}).get('error_type', 'Unknown')}")
    finally:
        agent_coder.cleanup()

if __name__ == "__main__":
    main()