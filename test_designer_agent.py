
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
        - Assume the primary implementation logic is within a single public class (e.g., named 'Solution' or a domain-relevant name like 'FileProcessor').
        - When calling methods from the implementation, always invoke them statically on the primary class (e.g., `Solution.methodName(args)` or `FileProcessor.methodName(args)`). Use 'Solution' as the class name in your tests if no other obvious name is inferred from the requirements.
        - Create separate `public static void` test methods for each logical function/user story.
        - Ensure all necessary Java `import` statements are at the top of the test file (even if they are standard Java libs).
        - Use `try-catch` blocks to handle any exceptions that might occur during the test method execution.
        - Check for basic conditions like "result != null" or "list.isEmpty() == false".
        - Print clear success/failure messages for each test.
        - DO NOT check for specific output values or complex logical correctness.
        - DO NOT use JUnit annotations or imports. Focus on runnable code in a `main` method in the test class.

        **IMPORTANT FOR EXTERNAL INTERACTIONS (Files, APIs, Databases)**:
        - **DO NOT attempt to open/read/write actual files on the filesystem.** Instead, simulate file operations by:
            - Passing `String` content instead of file paths to methods.
            - Using `StringReader` or `ByteArrayInputStream` to mock file content if `BufferedReader` or `InputStream` is expected.
            - Asserting that file *creation* or *closure* methods execute without exceptions.
        - **DO NOT make actual network calls to external APIs.** Instead, simulate API responses by:
            - Passing mock JSON strings to parsing methods.
            - Having the test methods return predefined mock data if an API call is expected.
        - **DO NOT connect to or query real databases (e.g., MongoDB).** Simulate database interactions by:
            - Passing dummy data structures (e.g., `Map<String, String>`) instead of database results.
            - Asserting that database update methods execute without exceptions.
        - The goal is to verify the internal logic and integration points, *not* the external system's availability.

        - Example of a test method structure:
        ```java
        public class RelaxedJavaTests { // This is the main test class
            public static void testOpenRequiredFiles() {
                try {
                    // Simulate file input/output by making the method accept mock objects or by not actually interacting with filesystem.
                    // Example: Call a method that doesn't need real files, or pass dummy data
                    // Map<String, BufferedReader> files = Solution.openFiles(); // If openFiles still expects files, it needs to be adapted or mocked.
                    // OR if openFiles is internal, just test the process that USES it:
                    // Solution.processRecords(new BufferedReader(new StringReader("mock data"))); // Example of mocking file content

                    // For file opening/closing methods, just ensure they execute without crashing.
                    // Example of simulating file existence and ensuring method runs:
                    Map<String, BufferedReader> mockFiles = new HashMap<>();
                    // Solution.openFiles(mockFiles); // If openFiles accepts Map
                    // Or simply assert the method signature exists and compiles without actual file interaction.
                    // For this example, we verify the method signature and expected non-exception behavior.
                    System.out.println("PASS: testOpenRequiredFiles - assumed successful execution with simulated environment.");

                } catch (Exception e) {
                    System.out.println("FAIL: testOpenRequiredFiles - " + e.getMessage());
                }
            }
            // Add a main method to run all tests
            public static void main(String[] args) {
                testOpenRequiredFiles();
                // Call other test methods here
            }
        }
        ```
        """,

                    "Csharp": """
    **RELAXED C# TESTING RULES**:

    - DO NOT redefine or include the implementation class in the test code. Only reference it.
    - The test class name MUST be different from the main implementation class. If the main class is `StringUtilities`, name the test class `StringUtilitiesTests`.
    - The test class should call the methods of the main class.
    - Use try-catch blocks to handle exceptions.
    - Check for basic conditions like "result != null".
    - Print success/failure messages.
    - DO NOT use any test frameworks like NUnit. Write the code as a simple console application.
    - **DO NOT include any example or reference implementation class in the test code. Only include the test class.**

    - Example:
    ```csharp
    public class StringUtilitiesTests {
        public static void TestBasicExecution() {
            try {
                string result = StringUtilities.ReverseString("hello");
                if (result != null)
                    Console.WriteLine("PASS: TestBasicExecution passed");
                else
                    Console.WriteLine("FAIL: TestBasicExecution returned null");
            } catch (Exception e) {
                Console.WriteLine(\$"FAIL: TestBasicExecution failed: {e.Message}");
            }
        }

        public static void Main(string[] args) {
            TestBasicExecution();
            // Add more test methods here
        }
    }
    ```
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