import json
import os

def analyze_results():
    try:
        with open('agentcoder_results_python.json', 'r') as f:
            results = json.load(f)

        print("=== AGENTCODER RESULTS ANALYSIS (Python) ===\n")

        print(f"Success: {results['success']}")
        print(f"Total Iterations: {results['iterations']}")
        print(f"Error: {results.get('error', 'N/A')}")

        if 'log' in results:
            print(f"\n=== ITERATION DETAILS ===")
            for i, iteration in enumerate(results['log']):
                print(f"\n--- Iteration {iteration['iteration']} ---")
                print(f"Code Length: {len(iteration['code'])} characters")
                print(f"Execution Success: {iteration['execution_result']['success']}")
                if not iteration['execution_result']['success']:
                    print(f"Error Type: {iteration['execution_result']['error_type']}")
                    print(f"Error: {iteration['execution_result']['error'][:200]}...")

        # Show the final code that was generated and save it
        if 'final_code' in results and results['final_code']:
            print(f"\n=== FINAL PYTHON CODE ===")
            print(results['final_code'])
            
            # Save the final Python code to a file
            output_file_name = "generated_python_code.py"
            with open(output_file_name, 'w') as f:
                f.write(results['final_code'])
            print(f"\nSuccessfully saved final Python code to {output_file_name}")

        # Show the tests that were used
        if 'tests' in results and results['tests']:
            print(f"\n=== TESTS USED (Python) ===")
            print(results['tests'])

    except FileNotFoundError:
        print("Results file 'agentcoder_results_python.json' not found. Make sure you've run the POC first.")
    except Exception as e:
        print(f"Error analyzing Python results: {e}")

def analyze_results_java():
    try:
        with open('agentcoder_results_java.json', 'r') as f:
            results = json.load(f)

        print("\n=== AGENTCODER RESULTS ANALYSIS (Java) ===\n")

        print(f"Success: {results['success']}")
        print(f"Total Iterations: {results['iterations']}")
        print(f"Error: {results.get('error', 'N/A')}")

        if 'log' in results:
            print(f"\n=== ITERATION DETAILS ===")
            for i, iteration in enumerate(results['log']):
                print(f"\n--- Iteration {iteration['iteration']} ---")
                print(f"Code Length: {len(iteration['code'])} characters")
                print(f"Execution Success: {iteration['execution_result']['success']}")
                if not iteration['execution_result']['success']:
                    print(f"Error Type: {iteration['execution_result']['error_type']}")
                    print(f"Error: {iteration['execution_result']['error'][:200]}...")

        # Show the final code that was generated and save it
        if 'final_code' in results and results['final_code']:
            print(f"\n=== FINAL JAVA CODE ===")
            print(results['final_code'])
            
            # Save the final Java code to a file
            # Assuming the Java code includes a class name, you might want to extract it
            # For simplicity, let's save to a generic name for now or try to parse class name
            java_code = results['final_code']
            class_name = "AgentCoderGenerated" # Default
            
            # A simple (and potentially fragile) way to extract class name for file naming
            import re
            match = re.search(r'public\s+class\s+([a-zA-Z0-9_]+)', java_code)
            if match:
                class_name = match.group(1)
            
            output_file_name = f"{class_name}.java"
            output_file_name = "generated_java_code.java"
            with open(output_file_name, 'w') as f:
                f.write(java_code)
            print(f"\nSuccessfully saved final Java code to {output_file_name}")

        # Show the tests that were used
        if 'tests' in results and results['tests']:
            print(f"\n=== TESTS USED (Java) ===")
            print(results['tests'])

    except FileNotFoundError:
        print("Results file 'agentcoder_results_java.json' not found. Make sure you've run the POC first.")
    except Exception as e:
        print(f"Error analyzing Java results: {e}")

if __name__ == "__main__":
    analyze_results()
    analyze_results_java()