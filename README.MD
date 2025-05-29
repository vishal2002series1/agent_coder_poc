# AgentCoder POC - Modular Python Code Generation with Compilation Feedback

This POC implements a multi-agent system for generating Python code with automatic testing and error feedback, based on the AgentCoder paper.

## Architecture

### 1. Programmer Agent
- Generates Python code based on requirements
- Refines code based on compilation/execution error feedback
- Uses Chain-of-Thought approach for code generation

### 2. Test Designer Agent  
- Creates comprehensive test cases independently from code
- Generates basic, edge, and large-scale test scenarios
- Ensures objective testing without code bias

### 3. Test Executor Agent
- Compiles and executes code with tests
- Provides detailed error feedback for refinement
- Handles timeouts and various error types

## Features

- ✅ Modular code generation with iterative refinement
- ✅ Independent test case generation
- ✅ Compilation error detection and feedback
- ✅ Runtime error handling with detailed feedback
- ✅ Configurable iteration limits
- ✅ Comprehensive logging and result tracking
- ✅ Azure OpenAI integration

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt