# test_designer_agent.py
import openai
from typing import Dict, Any, List
import json

class TestDesignerAgent:
    def __init__(self, api_key: str, endpoint: str, deployment: str, api_version: str):
        self.client = openai.AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version
        )
        self.deployment = deployment

    def generate_tests(self, requirements: str) -> Dict[str, Any]:
        """Generate comprehensive test cases for the given requirements"""

        prompt = f"""
**Role**: As a tester, create comprehensive test cases for the following requirements.

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

Please provide test cases as Python assert statements wrapped in ```python blocks.
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

            # Extract test code from response
            if "```python" in content:
                test_start = content.find("```python") + 9
                test_end = content.find("```", test_start)
                tests = content[test_start:test_end].strip()
            elif "```" in content:
                test_start = content.find("```") + 3
                test_end = content.find("```", test_start)
                tests = content[test_start:test_end].strip()
            else:
                tests = content.strip()

            return {
                "success": True,
                "tests": tests,
                "full_response": content
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tests": None
            }