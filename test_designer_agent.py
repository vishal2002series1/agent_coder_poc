# test_designer_agent.py (modified)
import openai
from typing import Dict, Any, List
from language_config import TargetLanguage, LanguageConfig

class TestDesignerAgent:
    def __init__(self, api_key: str, endpoint: str, deployment: str, api_version: str, target_language: TargetLanguage):
        self.client = openai.AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version
        )
        self.deployment = deployment
        self.target_language = target_language
        self.lang_config = LanguageConfig().get_config(target_language)

    def generate_tests(self, requirements: str) -> Dict[str, Any]:
        """Generate comprehensive test cases for the given requirements"""

        language_name = self.target_language.value.title()
        code_marker = self.lang_config["code_block_marker"]
        test_framework = self.lang_config["test_framework"]

        # Language-specific test instructions
        test_instructions = self._get_relaxed_test_instructions(language_name, test_framework)

        prompt = f"""
            **Role**: As a {language_name} tester, create RELAXED test cases for the following requirements.

            **Target Language**: {language_name}
            **Test Framework**: {test_framework}
            **Requirements**: {requirements}

            **IMPORTANT - RELAXED TESTING APPROACH**:
            - Focus ONLY on verifying that code executes without errors
            - DO NOT check for specific output values or mathematical precision
            - Use basic assertions like "not null", "not empty", or "no exceptions thrown"
            - The goal is to ensure the code runs on client systems, not functional correctness

            **Test Categories**:

            **1. Basic Execution Tests**:
            - Call each function with typical inputs
            - Verify the function returns something (not null/undefined)
            - Ensure no exceptions are thrown during normal execution

            **2. Edge Case Execution Tests**:
            - Test with edge inputs (empty, zero, negative values)
            - Verify the code handles these without crashing
            - Check that functions return some result (any result is acceptable)

            **3. Integration Tests**:
            - Test that different functions can be called together
            - Verify the overall program flow executes without errors

            {test_instructions}

            Please provide test cases wrapped in {code_marker} blocks.
            Focus on EXECUTION SUCCESS, not output correctness.
            """

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )

            content = response.choices[0].message.content
            tests = self._extract_code(content, code_marker)

            return {
                "success": True,
                "tests": tests,
                "full_response": content,
                "language": self.target_language.value
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tests": None,
                "language": self.target_language.value
            }

    # test_designer_agent.py (Updated _get_test_instructions method)
    def _get_test_instructions(self, language_name: str, test_framework: str) -> str:
        """Get language-specific test instructions"""
        instructions = {
            "Python": """
                Use Python assert statements.
                Example: assert function_name(input) == expected_output
                For exception testing:
                try:
                    function_name(invalid_input)
                    assert False, "Should have raised exception"
                except ExpectedException:
                    pass
                """,
                        "Java": """
                Create simple assertion-based tests that can run in main method.
                DO NOT use JUnit annotations or imports.
                Use simple assert statements and manual testing.
                Example:
                public static void testFunction() {
                    String result = functionName("input");
                    assert result.equals("expected") : "Test failed";
                }
                """,
                        "Csharp": """
                Create simple assertion-based tests that can run in Main method.
                DO NOT use NUnit or other testing frameworks.
                Use simple if statements and throw exceptions for failures.
                Example:
                static void TestFunction() {
                    string result = FunctionName("input");
                    if (result != "expected")
                        throw new Exception("Test failed");
                }
                """
                    }
        return instructions.get(language_name, "")
    

    def _get_relaxed_test_instructions(self, language_name: str, test_framework: str) -> str:
        """Get language-specific RELAXED test instructions"""
        instructions = {
                    "Python": """
            **RELAXED PYTHON TESTING RULES**:
            - Use try-except blocks to catch any exceptions
            - Check for basic conditions like "result is not None"
            - Print success/failure messages instead of strict assertions
            - Example:
            ```python
            def test_function():
                try:
                    result = function_name(input_value)
                    assert result is not None, "Function should return something"
                    print("PASS test_function passed")
                except Exception as e:
                    print(f"FAIL test_function failed: {e}")
                    """,

                    "Java": """
            **RELAXED JAVA TESTING RULES**:
            - Use try-catch blocks to handle exceptions gracefully
            - Check for basic conditions like "result != null"
            - Print success/failure messages
            - DO NOT use specific value assertions
            - DO NOT use JUnit annotations or imports
            - Example:
            public static void testFunction() {
                try {
                    String result = functionName("input");
                    assert result != null : "Function should return something";
                    System.out.println("PASS: testFunction");
                } catch (Exception e) {
                    System.out.println("FAIL: testFunction - " + e.getMessage());
                }
            }
            """,

                    "Csharp": """
            RELAXED C# TESTING RULES:

            Use try-catch blocks to handle exceptions
            Check for basic conditions like "result != null"
            Print success/failure messages
            Example:
            static void TestFunction() {
                try {
                    string result = FunctionName("input");
                    if (result == null)
                        throw new Exception("Function should return something");
                    Console.WriteLine("PASS TestFunction passed");
                } catch (Exception e) {
                    Console.WriteLine($"FAIL TestFunction failed: {e.Message}");
                }
            }
            """
        }
        return instructions.get(language_name, "")

    def _extract_code(self, content: str, code_marker: str) -> str:
        """Extract test code from response"""
        if code_marker in content:
            test_start = content.find(code_marker) + len(code_marker)
            test_end = content.find("```", test_start)
            tests = content[test_start:test_end].strip()
        elif "```" in content:
            test_start = content.find("```") + 3
            test_end = content.find("```", test_start)
            tests = content[test_start:test_end].strip()
        else:
            tests = content.strip()
        return tests