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
        test_instructions = self._get_test_instructions(language_name, test_framework)

        prompt = f"""
**Role**: As a {language_name} tester, create comprehensive test cases for the following requirements.

**Target Language**: {language_name}
**Test Framework**: {test_framework}
**Requirements**: {requirements}

**Instructions**:
Create test cases that cover:

**1. Basic Test Cases**:
- Verify fundamental functionality under normal conditions
- Test typical use cases and expected inputs

**2. Edge Test Cases**:
- Test boundary conditions and extreme cases
- Handle empty inputs, null values, edge boundaries
- Test unusual but valid inputs

**3. Large Scale Test Cases**:
- Test performance with large datasets
- Assess scalability and efficiency

{test_instructions}

Please provide test cases wrapped in {code_marker} blocks.
Include comments explaining each test scenario.
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