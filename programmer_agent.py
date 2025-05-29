# programmer_agent.py
import openai  # Import the OpenAI library
from typing import Dict, Any, Optional  # Import typing hints for better code readability
import json  # Import the JSON library for handling JSON data

class ProgrammerAgent:  # Define the ProgrammerAgent class
    def __init__(self, api_key: str, endpoint: str, deployment: str, api_version: str):
        # Initialize the ProgrammerAgent with Azure OpenAI credentials
        self.client = openai.AzureOpenAI(
            api_key=api_key,  # Your Azure OpenAI API key
            azure_endpoint=endpoint,  # Your Azure OpenAI endpoint
            api_version=api_version  # Your Azure OpenAI API version
        )
        self.deployment = deployment  # The deployment name for the OpenAI model

    def generate_code(self, requirements: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """Generate Python code based on requirements and optional feedback"""

        if feedback:
            prompt = f"""
**Role**: You are a software programmer.
**Task**: Fix the code based on the compilation/execution error feedback.

**Original Requirements**: {requirements}

**Error Feedback**: {feedback}

**Instructions**:
1. **Understand the Error**: Analyze the error message carefully
2. **Identify the Issue**: Determine what's causing the compilation/execution error
3. **Fix the Code**: Provide corrected Python code
4. **Ensure Modularity**: Write clean, modular code with proper imports

Please provide only the corrected Python code wrapped in ```python blocks.
"""
        else:
            prompt = f"""
**Role**: You are a software programmer.
**Task**: Generate Python code based on requirements using Chain-of-Thought approach.

**Requirements**: {requirements}

**Instructions**:
1. **Understand and Clarify**: Understand the task requirements
2. **Algorithm/Method Selection**: Choose the most efficient approach
3. **Pseudocode Creation**: Plan the implementation steps
4. **Code Generation**: Write clean, modular Python code

Please provide the Python code wrapped in ```python blocks.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,  # Use the specified deployment
                messages=[{"role": "user", "content": prompt}],  # Send the prompt to the OpenAI API
                temperature=0.1,  # Set the temperature for controlling randomness (lower is more deterministic)
                max_tokens=2000  # Set the maximum number of tokens in the response
            )

            content = response.choices[0].message.content  # Extract the content from the response

            # Extract code from response
            if "```python" in content:
                code_start = content.find("```python") + 9  # Find the start of the Python code block
                code_end = content.find("```", code_start)  # Find the end of the Python code block
                code = content[code_start:code_end].strip()  # Extract the code and remove leading/trailing whitespace
            elif "```" in content:
                code_start = content.find("```") + 3  # Find the start of the code block
                code_end = content.find("```", code_start)  # Find the end of the code block
                code = content[code_start:code_end].strip()  # Extract the code and remove leading/trailing whitespace
            else:
                code = content.strip()  # If no code block is found, extract the entire content and remove whitespace

            return {
                "success": True,  # Indicate that the code generation was successful
                "code": code,  # The generated code
                "full_response": content  # The full response from the OpenAI API
            }

        except Exception as e:
            return {
                "success": False,  # Indicate that the code generation failed
                "error": str(e),  # The error message
                "code": None  # No code was generated
            }