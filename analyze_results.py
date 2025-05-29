import json

def analyze_results():
    try:
        with open('agentcoder_results_python.json', 'r') as f:
            results = json.load(f)

        print("=== AGENTCODER RESULTS ANALYSIS ===\n")

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

        # Show the final code that was generated
        if 'final_code' in results and results['final_code']:
            print(f"\n=== FINAL CODE ===")
            print(results['final_code'])

        # Show the tests that were used
        if 'tests' in results and results['tests']:
            print(f"\n=== TESTS USED ===")
            print(results['tests'])

    except FileNotFoundError:
        print("Results file not found. Make sure you've run the POC first.")
    except Exception as e:
        print(f"Error analyzing results: {e}")

def analyze_results_java():
    try:
        with open('agentcoder_results_java.json', 'r') as f:
            results = json.load(f)

        print("=== AGENTCODER RESULTS ANALYSIS ===\n")

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

        # Show the final code that was generated
        if 'final_code' in results and results['final_code']:
            print(f"\n=== FINAL CODE ===")
            print(results['final_code'])

        # Show the tests that were used
        if 'tests' in results and results['tests']:
            print(f"\n=== TESTS USED ===")
            print(results['tests'])

    except FileNotFoundError:
        print("Results file not found. Make sure you've run the POC first.")
    except Exception as e:
        print(f"Error analyzing results: {e}")

if __name__ == "__main__":
    analyze_results()
    analyze_results_java()