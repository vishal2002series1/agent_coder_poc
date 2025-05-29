# test_executor_agent.py
import subprocess
import tempfile
import os
import sys
from typing import Dict, Any, Tuple
import traceback
import re

ALLOWED_PACKAGES = {"textblob", "nltk", "scikit-learn", "pandas", "numpy"}

class TestExecutorAgent:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()

    def execute_with_tests(self, code: str, tests: str) -> Dict[str, Any]:
        """Execute code with tests and return results with error feedback"""

        # Combine code and tests
        full_code = f"""{code}

# Test Cases
{tests}

print("All tests passed successfully!")
"""

        # First, try to compile the code
        compile_result = self._compile_code(full_code)
        if not compile_result["success"]:
            return {
                "success": False,
                "stage": "compilation",
                "error": compile_result["error"],
                "error_type": "SyntaxError",
                "feedback": f"Compilation Error: {compile_result['error']}"
            }

        # If compilation succeeds, try to execute
        execution_result = self._Code_Execution(full_code)
        return execution_result

    def _compile_code(self, code: str) -> Dict[str, Any]:
        """Check if code compiles without syntax errors"""
        try:
            compile(code, '<string>', 'exec')
            return {"success": True, "error": None}
        except SyntaxError as e:
            error_msg = f"Line {e.lineno}: {e.msg}"
            if e.text:
                error_msg += f"\nCode: {e.text.strip()}"
            return {"success": False, "error": error_msg}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # def _Code_Execution(self, code: str) -> Dict[str, Any]:
    #     """Execute the code and capture results"""

    #     # Create temporary file
    #     temp_file = os.path.join(self.temp_dir, "test_code.py")

    #     try:
    #         with open(temp_file, 'w') as f:
    #             f.write(code)

    #         # Execute the code
    #         result = subprocess.run(
    #             [sys.executable, temp_file],
    #             capture_output=True,
    #             text=True,
    #             timeout=30  # 30 second timeout
    #         )

    #         if result.returncode == 0:
    #             return {
    #                 "success": True,
    #                 "stage": "execution",
    #                 "output": result.stdout,
    #                 "error": None,
    #                 "feedback": "Code executed successfully!"
    #             }
    #         else:
    #             # Parse error for better feedback
    #             error_output = result.stderr
    #             error_type = self._parse_error_type(error_output)

    #             return {
    #                 "success": False,
    #                 "stage": "execution",
    #                 "error": error_output,
    #                 "error_type": error_type,
    #                 "feedback": f"Runtime Error ({error_type}): {error_output}"
    #             }

    #     except subprocess.TimeoutExpired:
    #         return {
    #             "success": False,
    #             "stage": "execution",
    #             "error": "Code execution timed out",
    #             "error_type": "TimeoutError",
    #             "feedback": "Code execution timed out (>30 seconds)"
    #         }
    #     except Exception as e:
    #         return {
    #             "success": False,
    #             "stage": "execution",
    #             "error": str(e),
    #             "error_type": "ExecutionError",
    #             "feedback": f"Execution Error: {str(e)}"
    #         }
    #     finally:
    #         # Cleanup
    #         if os.path.exists(temp_file):
    #             os.remove(temp_file)
    
    # def _Code_Execution(self, code: str) -> Dict[str, Any]:
    #     """Execute the code and capture results"""
    #     temp_file = os.path.join(self.temp_dir, "test_code.py")
    #     try:
    #         with open(temp_file, 'w') as f:
    #             f.write(code)

    #         result = subprocess.run(
    #             [sys.executable, temp_file],
    #             capture_output=True,
    #             text=True,
    #             timeout=30
    #         )

    #         if result.returncode == 0:
    #             return {
    #                 "success": True,
    #                 "stage": "execution",
    #                 "output": result.stdout,
    #                 "error": None,
    #                 "feedback": "Code executed successfully!"
    #             }
    #         else:
    #             error_output = result.stderr
    #             error_type = self._parse_error_type(error_output)

    #             # Enhanced feedback for AssertionError
    #             enhanced_feedback = error_output
    #             if "AssertionError" in error_output:
    #                 # Extract the line number from the error message
    #                 import re
    #                 match = re.search(r"line (\d+)", error_output)
    #                 line_number = int(match.group(1)) if match else None

    #                 # Read the content of the test file
    #                 with open(temp_file, 'r') as test_file:
    #                     test_lines = test_file.readlines()

    #                 # Extract the failing test line
    #                 failing_line = test_lines[line_number - 1].strip() if line_number else "N/A"

    #                 # Add the failing line to the feedback
    #                 enhanced_feedback += f"\n\nFailing Test Line: {failing_line}"

    #                 # Try to extract expected and actual values from the failing line
    #                 try:
    #                     import ast
    #                     tree = ast.parse(failing_line)
    #                     for node in ast.walk(tree):
    #                         if isinstance(node, ast.Compare):
    #                             left = ast.unparse(node.left)
    #                             ops = [type(op).__name__ for op in node.ops]
    #                             comparators = [ast.unparse(comp) for comp in node.comparators]

    #                             enhanced_feedback += f"\n\nComparison: {left} {ops[0]} {comparators[0]}"

    #                             # Try to evaluate the left and right sides
    #                             try:
    #                                 local_vars = {}
    #                                 exec(code, globals(), local_vars)  # Execute the generated code
    #                                 left_value = eval(left, globals(), local_vars)
    #                                 right_value = eval(comparators[0], globals(), local_vars)

    #                                 enhanced_feedback += f"\nActual: {left_value}"
    #                                 enhanced_feedback += f"\nExpected: {right_value}"

    #                                 # Compare lengths if they are lists
    #                                 if isinstance(left_value, list) and isinstance(right_value, list):
    #                                     enhanced_feedback += f"\nLength Actual: {len(left_value)}"
    #                                     enhanced_feedback += f"\nLength Expected: {len(right_value)}"

    #                             except Exception as e:
    #                                 enhanced_feedback += f"\nError during evaluation: {e}"

    #                 except Exception as e:
    #                     enhanced_feedback += f"\nError during parsing: {e}"

    #                 enhanced_feedback += "\n\nDEBUG INFO: This appears to be a test case failure. "
    #                 enhanced_feedback += "Please check if your function produces the exact expected output format and values. "
    #                 enhanced_feedback += "Consider edge cases and ensure your algorithm matches the test expectations."

    #             return {
    #                 "success": False,
    #                 "stage": "execution",
    #                 "error": error_output,
    #                 "error_type": error_type,
    #                 "feedback": f"Runtime Error ({error_type}): {enhanced_feedback}"
    #             }

    #     except subprocess.TimeoutExpired:
    #         return {
    #             "success": False,
    #             "stage": "execution",
    #             "error": "Code execution timed out",
    #             "error_type": "TimeoutError",
    #             "feedback": "Code execution timed out (>30 seconds). Your code might have an infinite loop or be too slow."
    #         }
    #     except Exception as e:
    #         return {
    #             "success": False,
    #             "stage": "execution",
    #             "error": str(e),
    #             "error_type": "ExecutionError",
    #             "feedback": f"Execution Error: {str(e)}"
    #         }
    #     finally:
    #         if os.path.exists(temp_file):
    #             os.remove(temp_file)

    def _Code_Execution(self, code: str) -> dict:
        temp_file = os.path.join(self.temp_dir, "test_code.py")
        try:
            with open(temp_file, 'w') as f:
                f.write(code)

            # 1. Parse import statements for external packages
            import_lines = re.findall(r"^\s*(?:import|from)\s+([a-zA-Z0-9_]+)", code, re.MULTILINE)
            packages = set(import_lines) & ALLOWED_PACKAGES

            # 2. Install allowed packages if needed
            if packages:
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", *packages],
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                except subprocess.CalledProcessError as e:
                    return {
                        "success": False,
                        "stage": "installation",
                        "error": e.stderr,
                        "error_type": "InstallationError",
                        "feedback": f"Package installation failed: {e.stderr}"
                    }

            # 3. Execute the code
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "stage": "execution",
                    "output": result.stdout,
                    "error": None,
                    "feedback": "Code executed successfully!"
                }
            else:
                error_output = result.stderr
                error_type = self._parse_error_type(error_output)
                return {
                    "success": False,
                    "stage": "execution",
                    "error": error_output,
                    "error_type": error_type,
                    "feedback": f"Runtime Error ({error_type}): {error_output}"
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stage": "execution",
                "error": "Code execution timed out",
                "error_type": "TimeoutError",
                "feedback": "Code execution timed out (>30 seconds)."
            }
        except Exception as e:
            return {
                "success": False,
                "stage": "execution",
                "error": str(e),
                "error_type": "ExecutionError",
                "feedback": f"Execution Error: {str(e)}"
            }
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def _parse_error_type(self, error_output: str) -> str:
        """Parse error type from error output"""
        if "AssertionError" in error_output:
            return "AssertionError"
        elif "NameError" in error_output:
            return "NameError"
        elif "TypeError" in error_output:
            return "TypeError"
        elif "ValueError" in error_output:
            return "ValueError"
        elif "ImportError" in error_output:
            return "ImportError"
        elif "IndentationError" in error_output:
            return "IndentationError"
        else:
            return "RuntimeError"

    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)