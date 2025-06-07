
from programmer_agent import ProgrammerAgent
from test_designer_agent import TestDesignerAgent
from test_executor_factory import TestExecutorFactory
from language_config import TargetLanguage
import os
from dotenv import load_dotenv
import json
import time
import ssl


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

        # Initialize retry-related attributes
        self._retry_previous_code = False
        self._previous_code = None

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
            # Check if we should retry the previous code (after dependency installation)
            if iteration > 1 and hasattr(self, '_retry_previous_code') and self._retry_previous_code:
                print(f"\n🔄 Iteration {iteration}: Retrying previous {language_name} code after dependency installation...")
                code = self._previous_code
                self._retry_previous_code = False  # Reset retry flag
            else:
                print(f"\n🔄 Iteration {iteration}: Generating {language_name} code...")

                # Pass comprehensive context to code generator
                code_result = self.programmer.generate_code_with_context(context)
                if not code_result["success"]:
                    print(f"❌ {language_name} code generation failed: {code_result['error']}")
                    continue
                code = code_result["code"]
                # print(f"--- Extracted code for {self.target_language.value} ---\n{code}\n--- End of code ---")
                print(f"✅ {language_name} code generated")

                # Store the code for potential retry
                self._previous_code = code

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
                # Clean up retry flags
                if hasattr(self, '_retry_previous_code'):
                    delattr(self, '_retry_previous_code')
                if hasattr(self, '_previous_code'):
                    delattr(self, '_previous_code')
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
                error_message = execution_result.get("error", "")

                print(f"❌ {error_stage.title()} failed ({error_type})")
                print(f"📋 Error: {error_message[:200]}...")

                # Check if this is a dependency-related error that might have been resolved
                is_dependency_error = self._is_dependency_error(error_type, error_message)
                was_retry_attempt = hasattr(self, '_retry_previous_code') and not self._retry_previous_code

                if is_dependency_error and not was_retry_attempt:
                    # This is a dependency error and we haven't retried yet
                    print(f"🔧 Dependency error detected. Will retry the same code in next iteration after dependency installation.")
                    self._retry_previous_code = True

                    # Don't add this to previous_attempts yet - we'll retry first
                    context["iteration_history"].append(iteration_log)
                else:
                    # Either not a dependency error, or retry failed - generate new code next time
                    print(f"🔄 Will generate new code in next iteration.")
                    if hasattr(self, '_retry_previous_code'):
                        self._retry_previous_code = False

                    # Update context with this failed attempt
                    context["previous_attempts"].append({
                        "iteration": iteration,
                        "code": code,
                        "error": error_message,
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

    def _is_dependency_error(self, error_type: str, error_message: str) -> bool:
            """
            Determine if an error is likely due to missing dependencies that might have been installed.
            """
            dependency_error_indicators = [
                "ModuleNotFoundError",
                "ImportError",
                "No module named",
                "cannot import name",
                "package not found"
            ]

            # Check error type
            if error_type in ["ImportError", "ModuleNotFoundError"]:
                return True

            # Check error message for dependency-related keywords
            error_lower = error_message.lower()
            for indicator in dependency_error_indicators:
                if indicator.lower() in error_lower:
                    return True

            return False


def main():
    # load_dotenv()

    # --- DEBUGGING .env LOAD START ---
    # Explicitly specify the path to your .env file
    # Assuming .env is in the same directory as agent_coder_poc.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    expected_dotenv_path = os.path.join(current_dir, '.env')

    if os.path.exists(expected_dotenv_path):
        dotenv_loaded = load_dotenv(dotenv_path=expected_dotenv_path, verbose=True, override=True)
        if dotenv_loaded:
            print(f"DEBUG: Explicitly loaded .env from: {expected_dotenv_path}")
        else:
            print(f"DEBUG: Failed to load .env from: {expected_dotenv_path}")
    else:
        print(f"DEBUG: Expected .env file not found at: {expected_dotenv_path}")
        load_dotenv(verbose=True, override=True) # Fallback to default search if explicit not found


    # --- DEBUGGING .env LOAD END ---

    debug_maven_path = os.getenv("MAVEN_EXECUTABLE_PATH")
    print(f"DEBUG: MAVEN_EXECUTABLE_PATH loaded from .env: {debug_maven_path}")

    config = {
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION")
    }

    # Example: Test with different languages
    # languages_to_test = [TargetLanguage.PYTHON, TargetLanguage.JAVA, TargetLanguage.CSHARP]
    languages_to_test = [TargetLanguage.CSHARP]
    # languages_to_test=[TargetLanguage.JAVA]

    requirements = """
    Create a function called 'reverse_string' that:
    1. Takes a string as input.
    2. Returns the reversed string.
    3. Handles edge cases like empty strings and null input.
    """

    requirements1 = """
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
    
    requirements1 = """
    Create a function called 'reverse_string' that:
    1. Takes a string as input.
    2. Returns the reversed string.
    3. Handles edge cases like empty strings and null input.
    4. It should be a complete code file with all the necessary imports and a main function to run the code.
    For example, if the target code is python, then the generated code should be a complete python file with the function defined and a main block to execute it.
    ** Avoid using string quotes in the code generation e.g '''python or ''' Java, as it can lead to issues with test case generation.
    ** It should be a complete code file with all the necessary imports and a main function to run the code.
    ** It should just not be a function definition, but a complete code file that can be executed directly.
    """

    requirements1 = '''As a developer, I want to implement file handling in Python to open, read, write, and close files (TCATBAL-FILE, XREF-FILE, DISCGRP-FILE, ACCOUNT-FILE, TRANSACT-FILE), so that data processing is seamless.

                    As a developer, I want to compute monthly interest using the formula (TRAN-CAT-BAL * DIS-INT-RATE) / 1200, so that interest calculations are accurate and follow business rules.

                    As a developer, I want to compute the total balance by adding TRAN-CAT-BAL and TRAN-INT-AMT, so that the final balance reflects both the category balance and interest. '''

    # requirements = "Implement a code to add two numbers."

    requirements = '''
[  { "Cloud" : AWS,
      " Database" : sqllite"
      "Files" : S3

}.
  {
    "epic_number": 1,
    "epic_description": "File Initialization and Management",
    "user_stories": [
      {
        "story_number": 1,
        "story_name": "Open Required Files for Processing",
        "story_description": "As a system, I need to open all required input and output files to ensure data is available for processing.",
        "story_details": "Implement file handling in Python to open the following files: `TCATBAL-FILE`, `XREF-FILE`, `DISCGRP-FILE`, `ACCOUNT-FILE`, and `TRANSACT-FILE`. Ensure proper error handling for file operations.",
        "story_type": "Technical",
        "legacy_component": "File Initialization"
      },
      {
        "story_number": 2,
        "story_name": "Close All Files After Processing",
        "story_description": "As a system, I need to close all opened files after processing to ensure data integrity and free up resources.",
        "story_details": "Implement file closure logic in Python for all opened files: `TCATBAL-FILE`, `XREF-FILE`, `DISCGRP-FILE`, `ACCOUNT-FILE`, and `TRANSACT-FILE`. Handle errors during file closure gracefully.",
        "story_type": "Technical",
        "legacy_component": "File Closure"
      }
    ]
  },
  {
    "epic_number": 2,
    "epic_description": "Record Processing and Data Retrieval",
    "user_stories": [
      {
        "story_number": 3,
        "story_name": "Process Records from Transaction Category Balance File",
        "story_description": "As a system, I need to loop through the `TCATBAL-FILE` and process each record to calculate interest and update accounts.",
        "story_details": "Implement a loop in Python to read records from `TCATBAL-FILE`. Increment the record count and check if the account ID has changed since the last record. If changed, update the account with accumulated interest and reset the total interest.",
        "story_type": "Functional",
        "legacy_component": "Record Processing"
      },
      {
        "story_number": 4,
        "story_name": "Retrieve Account and Cross-Reference Data",
        "story_description": "As a system, I need to fetch account and cross-reference data for each transaction to ensure accurate interest calculation.",
        "story_details": "Fetch account data from `ACCOUNT-FILE` and cross-reference data from `XREF-FILE` using the account ID. Implement MongoDB queries to retrieve the required data.",
        "story_type": "Functional",
        "legacy_component": "Data Retrieval"
      }
    ]
  },
  {
    "epic_number": 3,
    "epic_description": "Interest Calculation and Account Updates",
    "user_stories": [
      {
        "story_number": 5,
        "story_name": "Calculate Monthly Interest",
        "story_description": "As a system, I need to calculate monthly interest for each transaction to ensure accurate financial processing.",
        "story_details": "Retrieve the interest rate from `DISCGRP-FILE` using the account group ID and transaction category. If not found, use a default group code to fetch the default interest rate. Compute the monthly interest using the formula `(Transaction Balance * Interest Rate) / 1200` and accumulate the calculated interest.",
        "story_type": "Functional",
        "legacy_component": "Interest Calculation"
      },
      {
        "story_number": 6,
        "story_name": "Update Account Balances",
        "story_description": "As a system, I need to update account balances with the accumulated interest to reflect the latest financial data.",
        "story_details": "Add the accumulated interest to the current account balance. Reset the current cycle credit and debit amounts. Update the account record in MongoDB.",
        "story_type": "Functional",
        "legacy_component": "Account Update"
      }
    ]
  },
  {
    "epic_number": 4,
    "epic_description": "Transaction Record Creation",
    "user_stories": [
      {
        "story_number": 7,
        "story_name": "Create Transaction Records for Calculated Interest",
        "story_description": "As a system, I need to create transaction records for each calculated interest to maintain a record of financial activities.",
        "story_details": "Generate a transaction record for each calculated interest. Populate transaction details such as description, amount, and timestamps. Write the transaction record to the `TRANSACT-FILE` using MongoDB.",
        "story_type": "Functional",
        "legacy_component": "Transaction Record Creation"
      }
    ]
  },
  {
    "epic_number": 5,
    "epic_description": "Error Handling and Logging",
    "user_stories": [
      {
        "story_number": 8,
        "story_name": "Implement Error Handling for File Operations",
        "story_description": "As a system, I need to handle errors during file operations to ensure smooth processing and data integrity.",
        "story_details": "Use Python's `try-except` blocks to handle errors during file opening, reading, writing, and closure. Log errors using Python's `logging` module.",
        "story_type": "Technical",
        "legacy_component": "Error Handling"
      },
      {
        "story_number": 9,
        "story_name": "Log Errors and Exceptions",
        "story_description": "As a system, I need to log errors and exceptions in a structured format to facilitate debugging and monitoring.",
        "story_details": "Implement structured logging using Python's `logging` module. Log errors with details such as timestamp, error type, and affected file or record.",
        "story_type": "Technical",
        "legacy_component": "Error Logging"
      }
    ]
  }
  '''
    requirements1 = '''
  {
    "epic_number": 6,
    "epic_description": "External Service Integration and Data Processing",
    "user_stories": [
      {
        "story_number": 10,
        "story_name": "Fetch and Process Currency Exchange Rates from External API",
        "story_description": "As a system, when dealing with transactions in multiple currencies, I need to fetch the latest currency exchange rates from an external API and parse the data to enable accurate currency conversion within the application.",
        "story_details": "Implement a Java module responsible for fetching currency exchange rates. This module must: \n1. Connect to an external exchange rate API provider (e.g., a free service like ExchangeRate-API: `https://api.exchangerate-api.com/v4/latest/USD`, or an alternative public/mock API endpoint that returns JSON). \n2. Utilize a robust external HTTP client library such as **Apache HttpClient** or **OkHttp** to execute the HTTP GET request to the chosen API. Avoid using Java's basic `HttpURLConnection` for this task to ensure more advanced features like connection pooling and easier request/response handling are available if needed later. \n3. The API will return data in JSON format. Use a dedicated external JSON parsing library like **Jackson** or **Gson** to parse the JSON response into Java objects. Do not implement manual JSON string parsing. \n4. Extract the required exchange rates (e.g., rates relative to a base currency like USD) from the parsed Java objects. \n5. Implement comprehensive error handling for scenarios such as network failures, API errors (e.g., non-200 HTTP status codes), timeouts, and JSON parsing exceptions. Log errors using `java.util.logging` or a more advanced external logging framework if specified elsewhere. \n6. The fetched and parsed exchange rates should be made available to other parts of the system, for instance, to be used during interest calculation or transaction record creation for foreign currency transactions.",
        "story_type": "Functional",
        "legacy_component": "Currency Conversion Service Interface"
      }
    ]
  }
]
    '''

    requirements1 = '''

[
	{
		"epic_number": 1,
		"epic_description": "File Initialization and Closure",
		"user_stories": [
			{
				"story_number": 1,
				"story_name": "Initialize Input Files",
				"story_description": "As a system, I need to open all required input files to ensure data is available for processing.",
				"story_details": "Open the following files: TCATBAL-FILE, XREF-FILE, DISCGRP-FILE, ACCOUNT-FILE, TRANSACT-FILE using Python's file handling mechanisms.",
				"story_type": "Technical",
				"legacy_component": "File Initialization"
			},
			{
				"story_number": 2,
				"story_name": "Close Files After Processing",
				"story_description": "As a system, I need to close all opened files after processing to ensure proper resource management.",
				"story_details": "Close the following files: TCATBAL-FILE, XREF-FILE, DISCGRP-FILE, ACCOUNT-FILE, TRANSACT-FILE using Python's file handling mechanisms.",
				"story_type": "Technical",
				"legacy_component": "File Closure"
			}
		]
	},
	{
		"epic_number": 2,
		"epic_description": "Record Processing and Data Retrieval",
		"user_stories": [
			{
				"story_number": 3,
				"story_name": "Process Transaction Category Balance Records",
				"story_description": "As a system, I need to loop through all records in the TCATBAL-FILE to process transaction balances.",
				"story_details": "Implement a loop to read records sequentially from TCATBAL-FILE until the end of the file is reached.",
				"story_type": "Functional",
				"legacy_component": "Record Processing"
			},
			{
				"story_number": 4,
				"story_name": "Retrieve Account Data",
				"story_description": "As a system, I need to fetch account data from ACCOUNT-FILE using the account ID to ensure accurate processing.",
				"story_details": "Use Python's file handling and SQLite queries to retrieve account data based on the account ID.",
				"story_type": "Functional",
				"legacy_component": "Data Retrieval"
			},
			{
				"story_number": 5,
				"story_name": "Retrieve Cross-Reference Data",
				"story_description": "As a system, I need to fetch cross-reference data from XREF-FILE using the account ID to ensure accurate processing.",
				"story_details": "Use Python's file handling and SQLite queries to retrieve cross-reference data based on the account ID.",
				"story_type": "Functional",
				"legacy_component": "Data Retrieval"
			}
		]
	},
	{
		"epic_number": 3,
		"epic_description": "Interest Calculation and Account Update",
		"user_stories": [
			{
				"story_number": 6,
				"story_name": "Calculate Monthly Interest",
				"story_description": "As a system, I need to calculate monthly interest for each transaction balance using the predefined formula.",
				"story_details": "Implement the formula: Monthly Interest = (Transaction Balance * Interest Rate) / 1200. Retrieve interest rates from DISCGRP-FILE or use default group code if not found.",
				"story_type": "Functional",
				"legacy_component": "Interest Calculation"
			},
			{
				"story_number": 7,
				"story_name": "Update Account Balances",
				"story_description": "As a system, I need to update account balances with accumulated interest and reset cycle credit/debit amounts.",
				"story_details": "Add accumulated interest to the current account balance and reset cycle credit/debit amounts. Update the account record in ACCOUNT-FILE using SQLite.",
				"story_type": "Functional",
				"legacy_component": "Account Update"
			}
		]
	},
	{
		"epic_number": 4,
		"epic_description": "Transaction Record Creation",
		"user_stories": [
			{
				"story_number": 8,
				"story_name": "Create Transaction Records",
				"story_description": "As a system, I need to create transaction records for calculated interest to ensure proper tracking.",
				"story_details": "Generate transaction records with details such as description, amount, and timestamps. Write these records to TRANSACT-FILE using Python's file handling mechanisms.",
				"story_type": "Functional",
				"legacy_component": "Transaction Record Creation"
			}
		]
	},
	{
		"epic_number": 5,
		"epic_description": "Security and Scalability",
		"user_stories": [
			{
				"story_number": 9,
				"story_name": "Implement Security for File Access",
				"story_description": "As a system, I need to implement robust security mechanisms to ensure secure file access and data processing.",
				"story_details": "Use AWS IAM roles and policies to secure file access and implement encryption for sensitive data during processing.",
				"story_type": "Technical",
				"legacy_component": "Security"
			},
			{
				"story_number": 10,
				"story_name": "Ensure Scalability for Batch Processing",
				"story_description": "As a system, I need to ensure scalability to handle 10,000 transactions within 1 hour.",
				"story_details": "Optimize batch processing using Python multiprocessing or AWS Batch services to meet performance requirements.",
				"story_type": "Technical",
				"legacy_component": "Scalability"
			}
		]
	},
	{
		"epic_number": 6,
		"epic_description": "Disaster Recovery and High Availability",
		"user_stories": [
			{
				"story_number": 11,
				"story_name": "Implement Disaster Recovery Strategy",
				"story_description": "As a system, I need to implement a disaster recovery strategy to ensure batch job completion within the acceptable RTO and RPO.",
				"story_details": "Use AWS S3 for file backups and AWS RDS for database replication to ensure high availability and disaster recovery.",
				"story_type": "Technical",
				"legacy_component": "Disaster Recovery"
			}
		]
	}
]
'''
    requirements1 = '''
    Create a C# program that prints "Hello, C#!" to the console.

    '''

    requirements = '''

[
	{
		"epic_number": 1,
		"epic_description": "File Initialization and Closure",
		"user_stories": [
			{
				"story_number": 1,
				"story_name": "Initialize Input Files",
				"story_description": "As a system, I need to open all required input files to ensure data is available for processing.",
				"story_details": "Open the following files: TCATBAL-FILE, XREF-FILE, DISCGRP-FILE, ACCOUNT-FILE, TRANSACT-FILE using Python's file handling mechanisms.",
				"story_type": "Technical",
				"legacy_component": "File Initialization"
			},
			{
				"story_number": 2,
				"story_name": "Close Files After Processing",
				"story_description": "As a system, I need to close all opened files after processing to ensure proper resource management.",
				"story_details": "Close the following files: TCATBAL-FILE, XREF-FILE, DISCGRP-FILE, ACCOUNT-FILE, TRANSACT-FILE using Python's file handling mechanisms.",
				"story_type": "Technical",
				"legacy_component": "File Closure"
			}
		]
	},
	{
		"epic_number": 2,
		"epic_description": "Record Processing and Data Retrieval",
		"user_stories": [
			{
				"story_number": 3,
				"story_name": "Process Transaction Category Balance Records",
				"story_description": "As a system, I need to loop through all records in the TCATBAL-FILE to process transaction balances.",
				"story_details": "Implement a loop to read records sequentially from TCATBAL-FILE until the end of the file is reached.",
				"story_type": "Functional",
				"legacy_component": "Record Processing"
			},
			{
				"story_number": 4,
				"story_name": "Retrieve Account Data",
				"story_description": "As a system, I need to fetch account data from ACCOUNT-FILE using the account ID to ensure accurate processing.",
				"story_details": "Use Python's file handling and SQLite queries to retrieve account data based on the account ID.",
				"story_type": "Functional",
				"legacy_component": "Data Retrieval"
			},
			{
				"story_number": 5,
				"story_name": "Retrieve Cross-Reference Data",
				"story_description": "As a system, I need to fetch cross-reference data from XREF-FILE using the account ID to ensure accurate processing.",
				"story_details": "Use Python's file handling and SQLite queries to retrieve cross-reference data based on the account ID.",
				"story_type": "Functional",
				"legacy_component": "Data Retrieval"
			}
		]
	},
	{
		"epic_number": 3,
		"epic_description": "Interest Calculation and Account Update",
		"user_stories": [
			{
				"story_number": 6,
				"story_name": "Calculate Monthly Interest",
				"story_description": "As a system, I need to calculate monthly interest for each transaction balance using the predefined formula.",
				"story_details": "Implement the formula: Monthly Interest = (Transaction Balance * Interest Rate) / 1200. Retrieve interest rates from DISCGRP-FILE or use default group code if not found.",
				"story_type": "Functional",
				"legacy_component": "Interest Calculation"
			},
			{
				"story_number": 7,
				"story_name": "Update Account Balances",
				"story_description": "As a system, I need to update account balances with accumulated interest and reset cycle credit/debit amounts.",
				"story_details": "Add accumulated interest to the current account balance and reset cycle credit/debit amounts. Update the account record in ACCOUNT-FILE using SQLite.",
				"story_type": "Functional",
				"legacy_component": "Account Update"
			}
		]
	},
	{
		"epic_number": 4,
		"epic_description": "Transaction Record Creation",
		"user_stories": [
			{
				"story_number": 8,
				"story_name": "Create Transaction Records",
				"story_description": "As a system, I need to create transaction records for calculated interest to ensure proper tracking.",
				"story_details": "Generate transaction records with details such as description, amount, and timestamps. Write these records to TRANSACT-FILE using Python's file handling mechanisms.",
				"story_type": "Functional",
				"legacy_component": "Transaction Record Creation"
			}
		]
	},
	{
		"epic_number": 5,
		"epic_description": "Security and Scalability",
		"user_stories": [
			{
				"story_number": 9,
				"story_name": "Implement Security for File Access",
				"story_description": "As a system, I need to implement robust security mechanisms to ensure secure file access and data processing.",
				"story_details": "Use AWS IAM roles and policies to secure file access and implement encryption for sensitive data during processing.",
				"story_type": "Technical",
				"legacy_component": "Security"
			},
			{
				"story_number": 10,
				"story_name": "Ensure Scalability for Batch Processing",
				"story_description": "As a system, I need to ensure scalability to handle 10,000 transactions within 1 hour.",
				"story_details": "Optimize batch processing using Python multiprocessing or AWS Batch services to meet performance requirements.",
				"story_type": "Technical",
				"legacy_component": "Scalability"
			}
		]
	},
	{
		"epic_number": 6,
		"epic_description": "Disaster Recovery and High Availability",
		"user_stories": [
			{
				"story_number": 11,
				"story_name": "Implement Disaster Recovery Strategy",
				"story_description": "As a system, I need to implement a disaster recovery strategy to ensure batch job completion within the acceptable RTO and RPO.",
				"story_details": "Use AWS S3 for file backups and AWS RDS for database replication to ensure high availability and disaster recovery.",
				"story_type": "Technical",
				"legacy_component": "Disaster Recovery"
			}
		]
	}
]

'''

    
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
    ssl._create_default_https_context = ssl._create_unverified_context
    main()