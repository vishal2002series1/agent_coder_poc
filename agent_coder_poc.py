# agent_coder_poc.py (modified)
from programmer_agent_old import ProgrammerAgent
from test_designer_agent import TestDesignerAgent
from test_executor_factory import TestExecutorFactory
from language_config import TargetLanguage
import os
from dotenv import load_dotenv
import json
import time

class AgentCoderPOC:
    def __init__(self, config, target_language: TargetLanguage):
        self.target_language = target_language

        self.programmer = ProgrammerAgent(
            api_key=config["api_key"],
            endpoint=config["endpoint"],
            deployment=config["deployment"],
            api_version=config["api_version"],
            target_language=target_language
        )

        self.test_designer = TestDesignerAgent(
            api_key=config["api_key"],
            endpoint=config["endpoint"],
            deployment=config["deployment"],
            api_version=config["api_version"],
            target_language=target_language
        )

        self.test_executor = TestExecutorFactory.create_executor(target_language)
        self.max_iterations = 5
        self.results_log = []

    def generate_and_test_code(self, requirements):
        language_name = self.target_language.value.title()
        print(f"🚀 Starting AgentCoder POC for {language_name}: {requirements[:100]}...")

        # Step 1: Generate test cases
        print(f"\n📝 Step 1: Generating {language_name} test cases...")
        test_result = self.test_designer.generate_tests(requirements)
        if not test_result["success"]:
            return {"success": False, "error": "Failed to generate tests", "details": test_result}
        tests = test_result["tests"]
        print(f"✅ {language_name} test cases generated successfully")

        # Step 2: Iterative code generation and testing
        context = {
            "requirements": requirements,
            "tests": tests,
            "previous_attempts": [],
            "iteration_history": []
        }

        for iteration in range(1, self.max_iterations + 1):
            print(f"\n🔄 Iteration {iteration}: Generating {language_name} code...")

            # Pass comprehensive context to code generator
            code_result = self.programmer.generate_code_with_context(context)
            if not code_result["success"]:
                print(f"❌ {language_name} code generation failed: {code_result['error']}")
                continue
            code = code_result["code"]
            print(f"✅ {language_name} code generated")

            # Execute code with tests
            print(f"🧪 Testing {language_name} code...")
            execution_result = self.test_executor.execute_with_tests(code, tests)

            # Log this iteration
            iteration_log = {
                "iteration": iteration,
                "language": self.target_language.value,
                "code": code,
                "tests": tests,
                "execution_result": execution_result,
                "timestamp": time.time()
            }
            self.results_log.append(iteration_log)

            if execution_result["success"]:
                print(f"🎉 Success! {language_name} code passed all tests in iteration {iteration}")
                return {
                    "success": True,
                    "language": self.target_language.value,
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

                # Update context with this failed attempt
                context["previous_attempts"].append({
                    "iteration": iteration,
                    "code": code,
                    "error": execution_result["error"],
                    "error_type": error_type,
                    "error_stage": error_stage,
                    "feedback": execution_result.get("feedback", "")
                })

                context["iteration_history"].append(iteration_log)

        print(f"\n💥 Failed to generate working {language_name} code after {self.max_iterations} iterations")
        return {
            "success": False,
            "language": self.target_language.value,
            "error": "Max iterations reached without success",
            "final_code": code if 'code' in locals() else None,
            "tests": tests,
            "iterations": self.max_iterations,
            "last_execution_result": execution_result if 'execution_result' in locals() else None,
            "log": self.results_log
        }

    def save_results(self, results, filename=None):
        if filename is None:
            filename = f"agentcoder_results_{self.target_language.value}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"📁 Results saved to {filename}")

    def cleanup(self):
        self.test_executor.cleanup()

def main():
    load_dotenv()

    config = {
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION")
    }

    # Example: Test with different languages
    # languages_to_test = [TargetLanguage.PYTHON, TargetLanguage.JAVA, TargetLanguage.CSHARP]
    languages_to_test = [TargetLanguage.PYTHON, TargetLanguage.JAVA]
    # languages_to_test=[TargetLanguage.JAVA]

    requirements = """
    Create a function called 'reverse_string' that:
    1. Takes a string as input.
    2. Returns the reversed string.
    3. Handles edge cases like empty strings and null input.
    """

    requirements = """
        User Story: Automated Customer Account Status Update
        As a Customer Service Representative (CSR),
        I want to have our customer account statuses automatically updated based on their recent activity and payment history,
        So that I always see the most accurate status (e.g., 'Active', 'Delinquent', 'Suspended', 'Deactivated') without manual review, improving efficiency and reducing billing errors.

        Acceptance Criteria:

        Given a nightly batch process runs, When the COBOL program CUSTBAL01.CBL finishes processing daily customer transactions and payment records, Then the CUSTOMER_ACCOUNT_STATUS field in the CUSTOMER_MASTER_FILE (a VSAM file) must be updated according to the following rules:
        If a customer has made at least one payment in the last 30 days and has no outstanding balance older than 60 days, their status should be set to 'Active'.
        If a customer has an outstanding balance older than 60 days but less than 90 days, their status should be set to 'Delinquent'.
        If a customer has an outstanding balance older than 90 days or has had no payment activity for 90 consecutive days, their status should be set to 'Suspended'.
        If a customer's account has been 'Suspended' for 180 consecutive days without any payment or activity, their status should be set to 'Deactivated'.
        Given the batch process successfully updates statuses, Then an audit log file (CUSTSTAT.LOG) must be generated, detailing for each customer account whether their status was changed, from what (old status), to what (new status), and the reason for the change (e.g., "Payment received, balance cleared", "Balance overdue > 60 days").
        Given a critical error occurs during status updates (e.g., file access error, invalid data format), Then the process must gracefully abort, log the specific error to the CUSTSTAT.LOG file, and send an alert to the Operations team.

        ** Use the exact same field names and structure as in the tests for both code and test generation.

        """
    
    requirements = """
    Create a function called 'reverse_string' that:
    1. Takes a string as input.
    2. Returns the reversed string.
    3. Handles edge cases like empty strings and null input.
    """

    for target_language in languages_to_test:
        print(f"\n{'='*50}")
        print(f"Testing with {target_language.value.upper()}")
        print(f"{'='*50}")

        agent_coder = AgentCoderPOC(config, target_language)
        try:
            results = agent_coder.generate_and_test_code(requirements)
            agent_coder.save_results(results)

            if results["success"]:
                print(f"\n🎯 {target_language.value.upper()} SUCCESS SUMMARY:")
                print(f"   ✅ Iterations needed: {results['iterations']}")
                print(f"   📝 Final code length: {len(results['final_code'])} characters")
                print(f"   🧪 All tests passed!")
            else:
                print(f"\n❌ {target_language.value.upper()} FAILURE SUMMARY:")
                print(f"   💥 Failed after {results['iterations']} iterations")
                print(f"   📋 Last error: {results.get('last_execution_result', {}).get('error_type', 'Unknown')}")
        finally:
            agent_coder.cleanup()

if __name__ == "__main__":
    main()