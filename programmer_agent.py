
import openai
from typing import Dict, Any, Optional
from language_config import TargetLanguage, LanguageConfig
import re

class ProgrammerAgent:
    def __init__(self, api_key: str, endpoint: str, deployment: str, api_version: str, target_language: TargetLanguage):
        self.client = openai.AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version
        )
        self.deployment = deployment
        self.target_language = target_language
        self.lang_config = LanguageConfig().get_config(target_language)

    def generate_code_with_context(self, context):
        """Generate code with full context including previous attempts and errors"""
        requirements = context["requirements"]
        tests = context["tests"]
        previous_attempts = context["previous_attempts"]

        language_name = self.target_language.value.title()
        code_marker = self.lang_config["code_block_marker"]

        # Build a comprehensive prompt
#         prompt = f"""
# You are an expert programmer. Generate {language_name} code that satisfies the following requirements and passes all the provided tests.

# REQUIREMENTS:
# {requirements}

# TESTS TO PASS:
# {tests}

# IMPORTANT: Use the exact same field names and data structures as shown in the tests.
# """
        # Build a comprehensive prompt with language-specific instructions
        if self.target_language == TargetLanguage.JAVA:
            prompt = f"""
        You are an expert Java programmer. Generate a complete, runnable Java program that satisfies the following requirements and passes all the provided tests.

        REQUIREMENTS:
        {requirements}

        TESTS TO PASS:
        {tests}

        IMPORTANT JAVA REQUIREMENTS:
        - Your *main implementation class* should be named 'Solution' (or a name highly relevant to the primary requirement, e.g., 'CustomerAccountProcessor' for the current requirement). Use 'Solution' as a default if no obvious domain name is present.
        - The code MUST be enclosed in a public class.
        - If the requirements describe a core process or a single main operation, ensure it's encapsulated in a public static method (e.g., `public static void main(String[] args)` if it's an executable program, or `public static ReturnType methodName(Parameters)` if it's a utility function expected by tests).
        - **Always include all necessary import statements at the top of the file.**
        - Use the exact same field names and data structures as shown in the tests.
        - Generate clean, well-documented implementation code.
        - Ensure the class name and method signatures you define are consistent with how the tests would invoke them.
        ** Generated code should not contain any test cases. **
        ** Use dependencies supported by Maven Central only. Do not use any other libraries or frameworks. **

          
              """
        elif self.target_language == TargetLanguage.PYTHON:
            prompt = f"""
        You are an expert Python programmer. Generate Python code that satisfies the following requirements and passes all the provided tests.

        REQUIREMENTS:
        {requirements}

        TESTS TO PASS:
        {tests}

        IMPORTANT: Use the exact same field names and data structures as shown in the tests.
        - The class should contain a main method if necessary to run the code
        - Try to use cloud infra and database as provided in the requirements.
        -** Always incorporate cloud infrastructure provided in requirements. Eg AWS, GCP, Azure**
        - **Always include all necessary import statements at the top of the file**
        - Use the exact same field names and data structures as shown in the tests
        - Generate clean, well-documented implementation code
        - Make sure the class name matches what the tests expect
        ** Generated code should not contain any test cases. **
        """
        else:
            prompt = f"""
        You are an expert programmer. Generate {language_name} code that satisfies the following requirements and passes all the provided tests.

        REQUIREMENTS:
        {requirements}

        TESTS TO PASS:
        {tests}

        ** Generated code should not contain any test cases. **

        IMPORTANT: Use the exact same field names and data structures as shown in the tests.
        """
        # Add context from previous failed attempts
        if previous_attempts:
            prompt += "\n\nPREVIOUS FAILED ATTEMPTS:\n"
            for i, attempt in enumerate(previous_attempts[-3:], 1):  # Show last 3 attempts
                prompt += f"""
                Attempt {attempt.get('iteration', i)}:
                - Error Type: {attempt.get('error_type', 'Unknown')}
                - Error Stage: {attempt.get('error_stage', 'Unknown')}
                - Error Details: {str(attempt.get('error', ''))[:500]}...
                - Code that failed:
                ```{self.target_language.value}
                {str(attempt.get('code', ''))[:1000]}...

                """
            prompt += """
            THINK STEP BY STEP AND LEARN FROM THESE ERRORS:

            Fix the specific issues mentioned in the error messages
            Ensure field names match exactly between your code and the tests
            Handle edge cases properly
            Make sure your code structure is compatible with the test expectations
            if code is same as previous code, change the entire coding approach logic and try newer approach to solve the problem.
            
            """

        prompt += f"""
            Generate the {language_name} code wrapped in {code_marker} blocks.
            The code should be ready to run with the provided tests.
            ** Generated code should not contain any test cases. **
            """

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )

            content = response.choices[0].message.content

            # print(f"\n--- LLM raw response for {self.target_language.value} ---\n{content}\n--- End of LLM response ---\n")
            code = self._extract_code(content, code_marker)
            # Save LLM response and extracted code to a Markdown file for debugging
            with open(f"output_{self.target_language.value}.md", "a", encoding="utf-8") as f:
                f.write(f"\n## LLM Response ({self.target_language.value})\n\n```\n{content}\n```\n")
                f.write(f"\n## Extracted Code ({self.target_language.value})\n\n```\n{code}\n```\n")
            return {
                "success": True,
                "code": code,
                "full_response": content,
                "language": self.target_language.value
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "code": None,
                "language": self.target_language.value
            }

    def generate_code(self, requirements: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """Backward compatible method - generate code based on requirements and optional feedback"""

        # If no feedback, use simple context
        if not feedback:
            context = {
                "requirements": requirements,
                "tests": "",
                "previous_attempts": [],
                "iteration_history": []
            }
            return self.generate_code_with_context(context)

        # If feedback exists, create context with previous attempt
        context = {
            "requirements": requirements,
            "tests": "",
            "previous_attempts": [{
                "error": feedback,
                "error_type": "Unknown",
                "error_stage": "execution",
                "iteration": 1,
                "code": ""
            }],
            "iteration_history": []
        }
        return self.generate_code_with_context(context)

    def _extract_code(self, content: str, code_marker: str) -> str:
        """Extract code from response based on language marker"""
        if code_marker in content:
            code_start = content.find(code_marker) + len(code_marker)
            code_end = content.find("", code_start)               
            code = content[code_start:code_end].strip()           
        elif "" in content:
            code_start = content.find("") + 3               
            code_end = content.find("", code_start)
            code = content[code_start:code_end].strip()
        else:
            code = content.strip()
        return code
    
    
    def _extract_code(self, content: str, code_marker: str) -> str:
        # Try to extract code between the specific code block marker and ```
        pattern = re.compile(rf"{re.escape(code_marker)}\s*([\s\S]+?)\s*```", re.MULTILINE)
        match = pattern.search(content)
        if match:
            return match.group(1).strip()
        # Fallback: extract any code block
        pattern = re.compile(r"```[\w]*\s*([\s\S]+?)\s*```", re.MULTILINE)
        match = pattern.search(content)
        if match:
            return match.group(1).strip()
        # Fallback: return the whole content
        return content.strip()
