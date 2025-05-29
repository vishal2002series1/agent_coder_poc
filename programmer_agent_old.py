# programmer_agent.py (modified)
import openai
from typing import Dict, Any, Optional
from language_config import TargetLanguage, LanguageConfig

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

    def generate_code(self, requirements: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """Generate code based on requirements and optional feedback"""

        language_name = self.target_language.value.title()
        code_marker = self.lang_config["code_block_marker"]

        if feedback:
            prompt = f"""
**Role**: You are a {language_name} programmer.
**Task**: Fix the code based on the compilation/execution error feedback.

**Target Language**: {language_name}
**Original Requirements**: {requirements}
**Error Feedback**: {feedback}

**Instructions**:
1. **Understand the Error**: Analyze the error message carefully
2. **Identify the Issue**: Determine what's causing the compilation/execution error
3. **Fix the Code**: Provide corrected {language_name} code
4. **Ensure Best Practices**: Write clean, modular code following {language_name} conventions

Please provide only the corrected {language_name} code wrapped in {code_marker} blocks.
"""
        else:
            prompt = f"""
**Role**: You are a {language_name} programmer.
**Task**: Generate {language_name} code based on requirements using Chain-of-Thought approach.

**Target Language**: {language_name}
**Requirements**: {requirements}

**Instructions**:
1. **Understand and Clarify**: Understand the task requirements
2. **Algorithm/Method Selection**: Choose the most efficient approach for {language_name}
3. **Pseudocode Creation**: Plan the implementation steps
4. **Code Generation**: Write clean, modular {language_name} code following best practices

Please provide the {language_name} code wrapped in {code_marker} blocks.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )

            content = response.choices[0].message.content
            code = self._extract_code(content, code_marker)

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

    def _extract_code(self, content: str, code_marker: str) -> str:
        """Extract code from response based on language marker"""
        if code_marker in content:
            code_start = content.find(code_marker) + len(code_marker)
            code_end = content.find("```", code_start)
            code = content[code_start:code_end].strip()
        elif "```" in content:
            code_start = content.find("```") + 3
            code_end = content.find("```", code_start)
            code = content[code_start:code_end].strip()
        else:
            code = content.strip()
        return code
    
    def generate_code_with_context(self, context):
        """Generate code with full context including previous attempts and errors"""
        requirements = context["requirements"]
        tests = context["tests"]
        previous_attempts = context["previous_attempts"]

        # Build a comprehensive prompt
        prompt = f"""
    You are an expert programmer. Generate {self.target_language.value} code that satisfies the following requirements and passes all the provided tests.

    REQUIREMENTS:
    {requirements}

    TESTS TO PASS:
    {tests}

    IMPORTANT: Use the exact same field names and data structures as shown in the tests.
    """

        # Add context from previous failed attempts
        if previous_attempts:
            prompt += "\n\nPREVIOUS FAILED ATTEMPTS:\n"
            for i, attempt in enumerate(previous_attempts[-3:], 1):  # Show last 3 attempts
                prompt += f"""
    Attempt {attempt['iteration']}:
    - Error Type: {attempt['error_type']}
    - Error Stage: {attempt['error_stage']}
    - Error Details: {attempt['error'][:500]}...
    - Code that failed:
    ```{self.target_language.value}
    {attempt['code'][:1000]}...
    """

            prompt += """
    LEARN FROM THESE ERRORS:

    Fix the specific issues mentioned in the error messages
    Ensure field names match exactly between your code and the tests
    Handle edge cases properly
    Make sure your code structure is compatible with the test expectations
    """

        prompt += f"""
    Generate ONLY the {self.target_language.value} code (no explanations, no markdown formatting).
    The code should be ready to run with the provided tests.
    """

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )

            code = response.choices[0].message.content.strip()
            return {"success": True, "code": code}

        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_code(self, requirements, feedback=None):
        """Backward compatible method"""
        context = {
            "requirements": requirements,
            "tests": "",
            "previous_attempts": [{"error": feedback, "iteration": 1}] if feedback else [],
            "iteration_history": []
        }
        return self.generate_code_with_context(context)