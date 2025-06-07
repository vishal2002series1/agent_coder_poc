
from abc import ABC, abstractmethod
from typing import Dict, Any
import subprocess
import tempfile
import os
import sys
from language_config import TargetLanguage, LanguageConfig
import re
import requests
# from bs4 import BeautifulSoup  # Import BeautifulSoup
# print("Loaded test_executor_factory.py from:", __file__)
print("DEBUG: Loaded test_executor_factory.py from:", __file__)

def debug_csharp_methods():
    for name, obj in globals().items():
        if name == "CSharpTestExecutor":
            print("CSharpTestExecutor methods:", dir(obj))
debug_csharp_methods()

def extract_public_class_name(java_code: str) -> str:
    match = re.search(r'public\s+class\s+(\w+)', java_code)
    if match:
        return match.group(1)
    raise ValueError("No public class found in Java code.")

def remove_duplicate_implementation(test_code: str, class_name: str) -> str:
    """
    Removes any public class definition for the implementation class from the test code.
    This prevents compilation errors due to duplicate class definitions.
    """
    # This regex matches 'public class <class_name> { ... }' including all content inside the braces
    pattern = rf'public\s+class\s+{class_name}\s*\{{[^{{}}]*(?:\{{[^{{}}]*\}}[^{{}}]*)*\}}'
    cleaned_code = re.sub(pattern, '', test_code, flags=re.MULTILINE | re.DOTALL)
    return cleaned_code.strip()

def extract_csharp_class_name(code: str) -> str:
    """
    Extract the public class name from C# code.
    """
    match = re.search(r'public\s+class\s+(\w+)', code)
    if match:
        return match.group(1)
    return None

class BaseTestExecutor(ABC):
    def __init__(self, target_language: TargetLanguage):
        self.target_language = target_language
        self.lang_config = LanguageConfig().get_config(target_language)
        self.temp_dir = tempfile.mkdtemp()

    @abstractmethod
    def execute_with_tests(self, code: str, tests: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _compile_code(self, code: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _Code_Execution(self, code: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def install_dependencies(self, code: str):
        pass

    def cleanup(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

class PythonTestExecutor(BaseTestExecutor):
    def execute_with_tests(self, code: str, tests: str) -> Dict[str, Any]:
        self.install_dependencies(code)
        self.install_dependencies(tests)
        full_code = f"""{code}

# Test Cases
{tests}

print("All tests passed successfully!")
"""
        
        compile_result = self._compile_code(full_code)
        if not compile_result["success"]:
            return {
                "success": False,
                "stage": "compilation",
                "error": compile_result["error"],
                "error_type": "SyntaxError",
                "feedback": f"Compilation Error: {compile_result['error']}"
            }

        return self._Code_Execution(full_code)

    def _compile_code(self, code: str) -> Dict[str, Any]:
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

    def _Code_Execution(self, code: str) -> Dict[str, Any]:
        temp_file = os.path.join(self.temp_dir, f"test_code{self.lang_config['file_extension']}")
        try:
            with open(temp_file, 'w') as f:
                f.write(code)

            # result = subprocess.run(
            #     self.lang_config["execution_command"] + [temp_file],
            #     capture_output=True,
            #     text=True,
            #     timeout=self.lang_config["timeout"]
            # )
            result = subprocess.run(
            [sys.executable, temp_file],  # Use sys.executable instead of lang_config
            capture_output=True,
            text=True,
            timeout=self.lang_config["timeout"]
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
                return {
                    "success": False,
                    "stage": "execution",
                    "error": result.stderr,
                    "error_type": self._parse_error_type(result.stderr),
                    "feedback": f"Runtime Error: {result.stderr}"
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stage": "execution",
                "error": "Code execution timed out",
                "error_type": "TimeoutError",
                "feedback": "Code execution timed out"
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
        else:
            return "RuntimeError"
    def install_dependencies(self, code: str):
        # Find all import statements
        imports = re.findall(r'^\s*import (\w+)', code, re.MULTILINE)
        imports += re.findall(r'^\s*from (\w+)', code, re.MULTILINE)
        # List of standard libraries (partial, can be expanded)
        std_libs = {
            'os', 'sys', 're', 'datetime', 'math', 'json', 'time', 'random', 'collections', 'itertools', 'functools',
            'typing', 'subprocess', 'tempfile', 'shutil', 'unittest', 'threading', 'logging', 'pathlib', 'copy', 'csv'
        }
        to_install = [pkg for pkg in set(imports) if pkg not in std_libs]
        for pkg in to_install:
            try:
                print(f"Installing Python package: {pkg}")
                subprocess.run([sys.executable, "-m", "pip", "install", pkg], check=True)
            except Exception as e:
                print(f"Failed to install {pkg}: {e}")

# class JavaTestExecutor(BaseTestExecutor):
#     def execute_with_tests(self, code: str, tests: str) -> Dict[str, Any]:
#         # Combine code and tests for Java
#         full_code = self._combine_java_code_and_tests(code, tests)

#         compile_result = self._compile_code(full_code)
#         if not compile_result["success"]:
#             return {
#                 "success": False,
#                 "stage": "compilation",
#                 "error": compile_result["error"],
#                 "error_type": "CompilationError",
#                 "feedback": f"Compilation Error: {compile_result['error']}"
#             }

#         return self._Code_Execution(full_code)

#     def _combine_java_code_and_tests(self, code: str, tests: str) -> str:
#         # Extract class name from code
#         import re
#         class_match = re.search(r'public\s+class\s+(\w+)', code)
#         class_name = class_match.group(1) if class_match else "TestClass"

#         return f"""
#                     {code}

#                     // Test Cases
#                     {tests}

#                     public class TestRunner {{
#                         public static void main(String[] args) {{
#                             // Run tests here
#                             System.out.println("All tests passed successfully!");
#                         }}
#                     }}
#                     """

#     def _compile_code(self, code: str) -> Dict[str, Any]:
#         temp_file = os.path.join(self.temp_dir, "TestRunner.java")
#         try:
#             with open(temp_file, 'w') as f:
#                 f.write(code)

#             result = subprocess.run(
#                 self.lang_config["compile_command"] + [temp_file],
#                 capture_output=True,
#                 text=True,
#                 timeout=30
#             )

#             if result.returncode == 0:
#                 return {"success": True, "error": None}
#             else:
#                 return {"success": False, "error": result.stderr}

#         except Exception as e:
#             return {"success": False, "error": str(e)}

#     def _Code_Execution(self, code: str) -> Dict[str, Any]:
#         try:
#             result = subprocess.run(
#                 ["java", "-cp", self.temp_dir, "TestRunner"],
#                 capture_output=True,
#                 text=True,
#                 timeout=self.lang_config["timeout"]
#             )

#             if result.returncode == 0:
#                 return {
#                     "success": True,
#                     "stage": "execution",
#                     "output": result.stdout,
#                     "error": None,
#                     "feedback": "Code executed successfully!"
#                 }
#             else:
#                 return {
#                     "success": False,
#                     "stage": "execution",
#                     "error": result.stderr,
#                     "error_type": "RuntimeError",
#                     "feedback": f"Runtime Error: {result.stderr}"
#                 }

#         except Exception as e:
#             return {
#                 "success": False,
#                 "stage": "execution",
#                 "error": str(e),
#                 "error_type": "ExecutionError",
#                 "feedback": f"Execution Error: {str(e)}"
#             }

# test_executor_factory.py (Updated JavaTestExecutor)
        

class JavaTestExecutor(BaseTestExecutor):

    def __init__(self, target_language: TargetLanguage):
        super().__init__(target_language)
        self.classpath = ""  # Initialize empty classpath
        # Read Maven executable path from environment variable
        self.maven_executable = os.getenv("MAVEN_EXECUTABLE_PATH")
        if not self.maven_executable:
            print("ERROR: MAVEN_EXECUTABLE_PATH not found in environment variables. Maven operations will likely fail.")
            # Fallback to 'mvn' if not explicitly set, though this might still fail if PATH is not configured
            self.maven_executable = "mvn"
        elif not os.path.exists(self.maven_executable):
            print(f"WARNING: Maven executable not found at specified path from .env: {self.maven_executable}. Falling back to 'mvn' in PATH.")
            self.maven_executable = "mvn" # Fallback if path from .env is invalid
        self._junit_installed = False 
        self._resolved_artifacts_cache = {}

    def _detect_java_dependencies(self, error_message: str) -> list:
        """
        Detect missing Java dependencies from compilation errors.
        """
        missing_deps = []

        # Common patterns for missing Java dependencies
        patterns = [
            r"package ([\w\.]+) does not exist",
            r"cannot find symbol.*class (\w+)",
            r"error: package ([\w\.]+) does not exist",
            r"cannot find symbol.*symbol:\s*class\s*(\w+)"
        ]

        for pattern in patterns:
            matches = re.findall(pattern, error_message)
            missing_deps.extend(matches)

        return list(set(missing_deps))  # Remove duplicates


   

    def execute_with_tests(self, code: str, tests: str) -> Dict[str, Any]:
        self.install_dependencies(code)
        self.install_dependencies(tests)

        # Dynamically extract class names
        code_class_name = extract_public_class_name(code)
        tests_class_name = extract_public_class_name(tests)

        code_file = os.path.join(self.temp_dir, f"{code_class_name}.java")
        tests_file = os.path.join(self.temp_dir, f"{tests_class_name}.java")

        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)
        with open(tests_file, 'w', encoding='utf-8') as f:
            f.write(tests)

        compile_result = self._compile_code(code_file, tests_file) # Pass individual files
        if not compile_result["success"]:
            return {
                "success": False,
                "stage": "compilation",
                "error": compile_result["error"],
                "error_type": "CompilationError",
                "feedback": f"Compilation Error: {compile_result['error']}"
            }

        return self._Code_Execution(tests_class_name)

    def merge_java_code_and_tests(self, code: str, tests: str) -> str:
        """Merge Java code and tests, ensuring all imports are at the top"""
        imports = set(re.findall(r'^\s*import .+?;', code, re.MULTILINE) +
                     re.findall(r'^\s*import .+?;', tests, re.MULTILINE))
        code_wo_imports = re.sub(r'^\s*import .+?;\n?', '', code, flags=re.MULTILINE)
        tests_wo_imports = re.sub(r'^\s*import .+?;\n?', '', tests, flags=re.MULTILINE)
        return '\n'.join(imports) + '\n\n' + code_wo_imports + '\n' + tests_wo_imports

    
    def _compile_code(self, code_file: str, tests_file: str) -> Dict[str, Any]:
        try:
            compile_cmd = ["javac"]

            
            # Ensure current directory and all installed JARs are on the classpath for compilation
            full_classpath_parts = [self.temp_dir] # Always include the current directory first

            if self.classpath: # self.classpath holds all the downloaded JAR paths
                full_classpath_parts.append(self.classpath)

            compile_cmd.extend(["-cp", os.pathsep.join(full_classpath_parts)])

            compile_cmd.extend([code_file, tests_file])

            result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.temp_dir
            )

            if result.returncode == 0:
                return {"success": True, "error": None}
            else:
                return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    
        
    def _Code_Execution(self, tests_class_name: str) -> Dict[str, Any]:
        try:
            exec_cmd = ["java", "-ea"]

            # Ensure current directory and all installed JARs are on the classpath for execution
            full_classpath_parts = [self.temp_dir] # Always include the current directory first

            if self.classpath: # self.classpath holds all the downloaded JAR paths
                full_classpath_parts.append(self.classpath)

            exec_cmd.extend(["-cp", os.pathsep.join(full_classpath_parts)])

            exec_cmd.append(tests_class_name)

            result = subprocess.run(
                exec_cmd,
                capture_output=True,
                text=True,
                timeout=self.lang_config["timeout"],
                cwd=self.temp_dir
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
                return {
                    "success": False,
                    "stage": "execution",
                    "error": result.stderr,
                    "error_type": "RuntimeError",
                    "feedback": f"Runtime Error: {result.stderr}"
                }
        except Exception as e:
            return {
                "success": False,
                "stage": "execution",
                "error": str(e),
                "error_type": "ExecutionError",
                "feedback": f"Execution Error: {str(e)}"
            }

   
    def install_dependencies(self, code: str):
        """
        Dynamically extract and install Java dependencies.
        """
        # 1. Extract import statements
        imports = re.findall(r'^\s*import\s+([\w\.]+);', code, re.MULTILINE)

        # 2. Filter out standard Java libraries
        std_libs = {'java.util', 'java.io', 'java.time', 'java.lang', 'java.math', 'java.net', 'java.nio', 'java.text'}
        external_imports = [pkg for pkg in set(imports) if not any(pkg.startswith(std) for std in std_libs)]

        if external_imports: # Only print if there are actual external imports
            print(f"Detected external Java dependencies: {external_imports}")

        # Always attempt to install JUnit if external imports are detected or if it's the first run
        # This ensures JUnit is available for tests
        self._install_junit()

        # If you later want to auto-install other arbitrary dependencies using Maven,
        # this is where you'd iterate through external_imports and call a Maven command
        # like 'mvn dependency:get' for each. For now, we are focusing on JUnit.
        for package in external_imports:
            self._resolve_and_install_dependency(package) # This now just prints an info message


    def _resolve_and_install_dependency(self, package: str):
        """
        Attempt to resolve a Java package to a Maven artifact (groupId, artifactId, version)
        and install it using Maven CLI.
        This method is now more extensive in its search heuristics and error handling.
        """
        # Add to the set of packages already being processed to prevent infinite loops for circular dependencies
        # (though less likely with single import resolution)
        if package in self._resolved_artifacts_cache: # Check cache before expensive search
            print(f"INFO: Dependency '{package}' already resolved/processed. Skipping.")
            return

        # Heuristic mapping for common libraries based on import prefixes
        # This helps to quickly map common imports to their usual Maven GAVs (GroupId:ArtifactId:Version)
        heuristic_map = {
            "com.fasterxml.jackson.databind": ("com.fasterxml.jackson.core", "jackson-databind"),
            "com.fasterxml.jackson.core": ("com.fasterxml.jackson.core", "jackson-core"), # Add specific core for Jackson
            "com.fasterxml.jackson.annotation": ("com.fasterxml.jackson.core", "jackson-annotations"), # Add annotations for Jackson
            "com.google.gson": ("com.google.code.gson", "gson"),
            "org.apache.http": ("org.apache.httpcomponents", "httpclient"),
            "org.slf4j": ("org.slf4j", "slf4j-api"), # Common logging facade
            "ch.qos.logback": ("ch.qos.logback", "logback-classic"), # Logback implementation
            "org.apache.logging.log4j": ("org.apache.logging.log4j", "log4j-api"), # Log4j2 API
            "org.junit": ("junit", "junit"), # Though JUnit is handled by _install_junit, this is good for consistency in heuristics
            "java.sql": ("mysql", "mysql-connector-java"), # Example for database driver if LLM imports it
            # Add more heuristics as needed based on common LLM generations or expected libraries
        }

        artifact = None
        inferred_group_id = None
        inferred_artifact_id = None
        search_query_used = ""

        print(f"\nAttempting to resolve dependency for package: {package}")

        # 1. Try heuristic mapping first (most common and usually fastest)
        for prefix, (g_id, a_id) in heuristic_map.items():
            if package.startswith(prefix):
                inferred_group_id = g_id
                inferred_artifact_id = a_id
                search_query_used = f"g:{inferred_group_id} AND a:{inferred_artifact_id}"
                print(f"INFO: Heuristically inferred GAV for {package}: {inferred_group_id}:{inferred_artifact_id}")
                # Try to get the latest version for this inferred GAV
                artifact = self._search_maven_central(search_query_used)
                if artifact:
                    print(f"DEBUG: Artifact found via heuristic: {artifact}")
                    break # Found a match, use it
                else:
                    print(f"WARNING: Heuristic GAV {inferred_group_id}:{inferred_artifact_id} not found on Maven Central. Trying generic search.")

        # 2. If heuristic fails or no direct match, try searching by Fully Qualified Class Name (FQCN)
        if not artifact:
            search_query_used = f"fc:{package}" # 'fc' for Fully Qualified Class Name search
            print(f"Attempting generic Maven Central search by FQCN: {search_query_used}")
            artifact = self._search_maven_central(search_query_used)

        # 3. If FQCN search fails, try a broader search by just the last component of the package name
        if not artifact:
            last_component = package.split('.')[-1]
            if len(last_component) > 2: # Avoid very short, common words that give too many irrelevant results
                search_query_used = last_component
                print(f"FQCN search failed, trying broader search by last package component: {search_query_used}")
                artifact = self._search_maven_central(search_query_used)


        # 4. If an artifact is found, download it and update classpath
        if artifact:
            print(f"Found Maven artifact for {package}: {artifact}")
            jar_paths = self._download_jar(artifact) # Now returns a list of paths

            if jar_paths: # Check if the list of paths is not empty
                print(f"✓ Successfully installed {package} with {len(jar_paths)} JARs.")
                for path in jar_paths: # Loop through each path in the list
                    self._update_classpath(path) # Add each individual JAR path to classpath
                self._resolved_artifacts_cache[package] = artifact # Cache the package-to-artifact mapping
            else:
                print(f"✗ Failed to download JARs for {package} using Maven. Check Maven output above.")
        else:
            # This 'else' block remains the same as before
            print(f"✗ Could not find Maven artifact for package: {package} after all attempts. This dependency will likely cause compilation failure.")
            print("Consider manually adding this dependency to a pom.xml or checking Maven Central manually.")


    def _search_maven_central(self, query: str) -> dict:
        """
        Search Maven Central JSON API for a given query and return artifact information.
        Query can be a package name, or a Solr query like "g:groupId AND a:artifactId".
        """
        # Check cache first
        if query in self._resolved_artifacts_cache:
            print(f"DEBUG: Using cached artifact for query: {query}")
            return self._resolved_artifacts_cache[query]

        search_url = f"https://search.maven.org/solrsearch/select?q={query}&rows=1&wt=json"
        # Best Practice: Use a User-Agent header to avoid being blocked by some APIs
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

        try:
            print(f"Searching Maven Central for: {query}")
            response = requests.get(search_url, headers=headers, timeout=10, verify=False) # Add timeout
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json() # Parse as JSON

            if data and 'response' in data and 'docs' in data['response'] and data['response']['docs']:
                doc = data['response']['docs'][0]
                artifact = {
                    'groupId': doc.get('g'),
                    'artifactId': doc.get('a'),
                    'version': doc.get('latestVersion') or doc.get('v') # Prefer latestVersion, fallback to 'v'
                }
                self._resolved_artifacts_cache[query] = artifact # Cache the result
                return artifact
            else:
                print(f"No artifact found for query: {query}")
                return None

        except requests.exceptions.Timeout:
            print(f"Error: Maven Central search timed out for {query}.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error searching Maven Central for {query}: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during Maven Central search for {query}: {e}")
            return None
        
    # def _download_jar(self, artifact: dict) -> str:
    #     """
    #     Download JAR file using Maven's dependency:get command.
    #     Returns the path to the downloaded JAR in the local Maven repository.
    #     """
    #     if not artifact or not artifact.get('groupId') or not artifact.get('artifactId') or not artifact.get('version'):
    #         print(f"ERROR: Invalid artifact provided for download: {artifact}")
    #         return None

    #     group_id = artifact['groupId']
    #     artifact_id = artifact['artifactId']
    #     version = artifact['version']

    #     # Construct the expected path in the local Maven repository (best practice for lookup)
    #     # This is where 'mvn dependency:get' puts the artifact.
    #     local_repo_root = os.path.join(os.path.expanduser("~"), ".m2", "repository")
    #     artifact_dir = os.path.join(
    #         local_repo_root,
    #         group_id.replace('.', os.sep), # Replace dots with OS-specific separator for directory structure
    #         artifact_id,
    #         version
    #     )
    #     expected_jar_path = os.path.join(artifact_dir, f"{artifact_id}-{version}.jar")

    #     # Check if the JAR already exists locally before calling Maven
    #     if os.path.exists(expected_jar_path):
    #         print(f"✓ {group_id}:{artifact_id}:{version} already exists in local Maven repo, skipping download.")
    #         return expected_jar_path

    #     print(f"Downloading {group_id}:{artifact_id}:{version} using Maven CLI...")
    #     try:
    #         # Using 'dependency:get' to download and place in local repo
    #         # '-Dtransitive=false' downloads only the direct artifact, not its dependencies.
    #         # This is good for individual import resolution to avoid pulling many unneeded JARs.
    #         cmd = [
    #             self.maven_executable,
    #             "dependency:get",
    #             f"-DgroupId={group_id}",
    #             f"-DartifactId={artifact_id}",
    #             f"-Dversion={version}",
    #             # "-Dtransitive=false",
    #             "-B" # Batch mode (less verbose output for CLI)
    #         ]

    #         result = subprocess.run(
    #             cmd,
    #             cwd=self.temp_dir, # Run from temp directory, though Maven operates on local repo
    #             capture_output=True,
    #             text=True,
    #             timeout=180 # Increased timeout for potential large downloads over slow networks
    #         )

    #         if result.returncode == 0:
    #             if os.path.exists(expected_jar_path):
    #                 print(f"✓ Downloaded {group_id}:{artifact_id}:{version} to local Maven repo.")
    #                 return expected_jar_path
    #             else:
    #                 # This case should ideally not happen if Maven reports success, but added for robustness.
    #                 print(f"✗ Maven get succeeded but JAR not found at expected path: {expected_jar_path}.")
    #                 print(f"Maven STDOUT: {result.stdout}")
    #                 print(f"Maven STDERR: {result.stderr}")
    #                 return None
    #         else:
    #             print(f"✗ Maven dependency:get failed for {group_id}:{artifact_id}:{version}.")
    #             print(f"Maven STDOUT: {result.stdout}")
    #             print(f"Maven STDERR: {result.stderr}")
    #             return None

    #     except subprocess.TimeoutExpired:
    #         print(f"✗ Maven dependency:get timed out for {group_id}:{artifact_id}:{version}.")
    #         return None
    #     except Exception as e:
    #         print(f"✗ Error during Maven dependency:get for {group_id}:{artifact_id}:{version}: {str(e)}")
    #         return None
        
    def _download_jar(self, artifact: dict) -> list[str]: # Return a list of paths
        """
        Download JAR files (including transitives) for an artifact using Maven's
        dependency:copy-dependencies to a dedicated 'lib' folder within temp_dir.
        Returns a list of paths to all downloaded JARs.
        """
        if not artifact or not artifact.get('groupId') or not artifact.get('artifactId') or not artifact.get('version'):
            print(f"ERROR: Invalid artifact provided for download: {artifact}")
            return []
        group_id = artifact['groupId']
        artifact_id = artifact['artifactId']
        version = artifact['version']

        # Create a dedicated output directory for this artifact's dependencies.
        # This helps avoid conflicts and makes it easy to add all copied JARs to the classpath.
        artifact_lib_dir = os.path.join(self.temp_dir, "lib", f"{artifact_id}-{version}")
        os.makedirs(artifact_lib_dir, exist_ok=True)

        # --- Idempotency Check (important for efficiency) ---
        # If the artifact_lib_dir exists and contains at least one JAR, assume it was already copied.
        # This is a heuristic to prevent redundant Maven calls.
        if os.path.exists(artifact_lib_dir) and any(f.endswith('.jar') for f in os.listdir(artifact_lib_dir)):
            print(f"✓ Dependencies for {group_id}:{artifact_id}:{version} already copied to {artifact_lib_dir}, skipping.")
            # Return paths to all JARs already in this directory
            return [os.path.join(artifact_lib_dir, f) for f in os.listdir(artifact_lib_dir) if f.endswith('.jar')]
        print(f"Copying dependencies for {group_id}:{artifact_id}:{version} to {artifact_lib_dir} using Maven CLI...")

        try:  # <--- Make sure this 'try' block is added here if it's not already
            # --- Dynamically create a minimal pom.xml for this specific artifact ---
            # 'dependency:copy-dependencies' needs a pom.xml to know what to copy.
            # Use a raw string literal (r"""...""") for the XML content.
            pom_content = (
                f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<project xmlns="http://maven.apache.org/POM/4.0.0"\n'
                f'         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                f'         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0\n'
                f'         http://maven.apache.org/xsd/maven-4.0.0.xsd">\n'
                f'    <modelVersion>4.0.0</modelVersion>\n'
                f'    <groupId>com.temp.agentcoder</groupId>\n'
                f'    <artifactId>temp-artifact-copier-{artifact_id}</artifactId>\n'
                f'    <version>1.0</version>\n'
                f'    <properties>\n'
                f'        <maven.compiler.source>11</maven.compiler.source>\n'
                f'        <maven.compiler.target>11</maven.compiler.target>\n'
                f'    </properties>\n'
                f'    <dependencies>\n'
                f'        <dependency>\n'
                f'            <groupId>{group_id}</groupId>\n'
                f'            <artifactId>{artifact_id}</artifactId>\n'
                f'            <version>{version}</version>\n'
                f'        </dependency>\n'
                f'    </dependencies>\n'
                f'</project>'
            )

            # Save the temporary pom.xml in our working temp_dir
            temp_pom_path = os.path.join(self.temp_dir, f"pom_{artifact_id}_{version}.xml")
            with open(temp_pom_path, 'w') as f:
                f.write(pom_content)
            # --- Construct the Maven command ---
            # Using 'dependency:copy-dependencies' to copy into our temp dir.
            # This will copy the artifact AND all its transitive dependencies.
            cmd = [
                self.maven_executable,
                "-f", 
                temp_pom_path, #  dynamically generated pom
                "dependency:copy-dependencies",
                f"-DoutputDirectory={artifact_lib_dir}", # Target directory for copied JARs
                "-DexcludeTransitive=false", # Explicitly include transitive dependencies (default behavior)
                "-B" # Batch mode (less verbose output for CLI)
            ]

            # --- Execute Maven command ---
            # Crucial: run from the directory that contains the temporary pom.xml
            result = subprocess.run(
                cmd,
                cwd=self.temp_dir, # Maven must be run from where it can find the pom.xml
                capture_output=True,
                text=True,
                timeout=300 # Increased timeout considerably for first-time full dependency download
            )

            # --- Process results ---
            if result.returncode == 0:
                # Collect all JARs that were copied to the artifact_lib_dir
                copied_jars = [os.path.join(artifact_lib_dir, f) for f in os.listdir(artifact_lib_dir) if f.endswith('.jar')]
                if copied_jars:
                    print(f"✓ Copied {len(copied_jars)} JARs for {group_id}:{artifact_id}:{version} to {artifact_lib_dir}.")
                    return copied_jars
                else:
                    print(f"✗ Maven copy-dependencies succeeded but no JARs found in {artifact_lib_dir}.")
                    print(f"Maven STDOUT: {result.stdout}")
                    print(f"Maven STDERR: {result.stderr}")
                    return []
            else:
                print(f"✗ Maven dependency:copy-dependencies failed for {group_id}:{artifact_id}:{version}.")
                print(f"Maven STDOUT: {result.stdout}")
                print(f"Maven STDERR: {result.stderr}")
                return []
        except subprocess.TimeoutExpired:
            print(f"✗ Maven dependency:copy-dependencies timed out for {group_id}:{artifact_id}:{version}.")
            return []
        except Exception as e:
            print(f"✗ Error during Maven dependency:copy-dependencies for {group_id}:{artifact_id}:{version}: {str(e)}")
            return []    



    def _update_classpath(self, jar_path: str):
        """
        Update the classpath with the given JAR path.
        """
        if not hasattr(self, 'classpath') or not self.classpath:
            self.classpath = jar_path
        else:
            self.classpath += os.pathsep + jar_path

    def _install_junit(self):
        """Install JUnit using Maven via the common _download_jar mechanism."""
        if self._junit_installed:
            print("JUnit already installed for this session, skipping.")
            return

        print("Installing JUnit...")
        junit_artifact = {
            'groupId': 'junit',
            'artifactId': 'junit',
            'version': '4.13.2' # Or use a search to get latest if desired, but 4.13.2 is standard for tests
        }

        try:
            # Use the general _download_jar method for JUnit as well
            jar_paths = self._download_jar(junit_artifact)

            if jar_paths:
                for path in jar_paths:
                    self._update_classpath(path)
                self._junit_installed = True
                print("✓ JUnit installed successfully via _download_jar.")
            else:
                print("✗ Failed to install JUnit: No JARs copied by Maven.")
        except Exception as e:
            print(f"✗ Error installing JUnit: {e}")


    def _install_testng(self):
        """Install TestNG using Maven"""
        # Similar implementation for TestNG
        print("TestNG installation not implemented yet")


class CSharpTestExecutor(BaseTestExecutor):

    
    @staticmethod
    def extract_namespaces_from_usings(code: str):
        """
        Extracts all namespaces from 'using' statements in the code.
        """
        return set(re.findall(r'^\s*using ([\w\.]+);', code, re.MULTILINE))
    
    # def install_dependencies(self, code: str):
    #     """
    #     Dynamically install NuGet packages based on code analysis.
    #     """
    #     # 1. Extract namespaces from 'using' statements
    #     namespaces = CSharpTestExecutor.extract_namespaces_from_usings(code)  # Call the static method
        
    #     print("Namespaces found:", namespaces)  # Print the namespaces for verification

    def install_dependencies(self, code: str):
        namespaces = CSharpTestExecutor.extract_namespaces_from_usings(code)
        print("Namespaces found:", namespaces)

        std_libs = {
            'System', 'System.Collections', 'System.Collections.Generic', 'System.IO', 'System.Linq',
            'System.Text', 'System.Threading', 'System.Net'
        }

        for ns in namespaces:
            if ns in std_libs:
                continue  # Skip standard libraries

            # Try to install a package with the same name as the namespace
            print(f"Trying to install NuGet package: {ns}")
            result = subprocess.run(
                ["dotnet", "add",  "package", ns],
                cwd=self.temp_dir,  # Ensure command is run in temp directory
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"✓ Installed {ns}")
                continue  # Success!

            # If direct install fails, search NuGet
            print(f"Direct install failed for {ns}. Searching NuGet...")
            package = self.search_nuget_by_namespace(ns)
            if package:
                print(f"Found NuGet package '{package}' for namespace '{ns}', installing...")
                result2 = subprocess.run(
                    ["dotnet", "add", "package", package],
                    cwd=self.temp_dir,  # Ensure command is run in temp directory
                    capture_output=True, text=True
                )
                if result2.returncode == 0:
                    print(f"✓ Installed {package}")
                else:
                    print(f"✗ Failed to install {package}: {result2.stderr}")
            else:
                print(f"✗ Could not resolve NuGet package for namespace: {ns}")

    def search_nuget_by_namespace(self, namespace):
        url = f"https://api-v2v3search-0.nuget.org/query?q={namespace}&prerelease=false"
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if data['totalHits'] > 0:
                return data['data'][0]['id']
        except Exception as e:
            print(f"NuGet search failed: {e}")
        return None

    def _create_csproj(self, project_dir):
        csproj_content = """
            <Project Sdk="Microsoft.NET.Sdk">
            <PropertyGroup>
                <OutputType>Exe</OutputType>
                <TargetFramework>net6.0</TargetFramework>
            </PropertyGroup>
            </Project>
            """
        with open(os.path.join(project_dir, "TestProject.csproj"), 'w') as f:
            f.write(csproj_content)

    @staticmethod
    def extract_usings(code: str) -> (list, str):
        """
        Extracts all using statements and returns (list_of_usings, code_without_usings)
        """
        usings = re.findall(r'^\s*using [\w\.]+;\s*', code, re.MULTILINE)
        code_wo_usings = re.sub(r'^\s*using [\w\.]+;\s*', '', code, flags=re.MULTILINE)
        return usings, code_wo_usings

    def execute_with_tests(self, code: str, tests: str) -> Dict[str, Any]:
        self.install_dependencies(code)
        self.install_dependencies(tests)
        
        # Extract the implementation class name
        implementation_class_name = extract_csharp_class_name(code)
        
        # Remove any duplicate implementation class from test code
        if implementation_class_name:
            print(f"DEBUG: Checking for duplicate '{implementation_class_name}' class in test code...")
            original_test_length = len(tests)
            tests = remove_duplicate_implementation(tests, implementation_class_name)
            if len(tests) < original_test_length:
                print(f"DEBUG: Removed duplicate '{implementation_class_name}' class from test code.")
        
        project_dir = self.temp_dir
        source_file = os.path.join(project_dir, "Program.cs")

        
        
        # In execute_with_tests:
        impl_usings, code_wo_usings = self.extract_usings(code)
        test_usings, tests_wo_usings = self.extract_usings(tests)
        all_usings = sorted(set(impl_usings + test_usings))  # Deduplicate and sort for neatness

        combined_code = ''.join(all_usings) + '\n' + code_wo_usings.strip() + '\n\n' + tests_wo_usings.strip()

        with open(source_file, 'w') as f:
            f.write(combined_code)
        
        # Create .csproj file
        self._create_csproj(project_dir)
        
        # Compile
        compile_result = self._compile_code(project_dir)
        if not compile_result["success"]:
            return {
                "success": False,
                "stage": "compilation",
                "error": compile_result["error"],
                "error_type": "CompilationError",
                "feedback": f"Compilation Error: {compile_result['error']}"
            }
        
        # Run
        return self._Code_Execution(project_dir)
    def _compile_code(self, project_dir: str) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ["dotnet", "build", project_dir],
                cwd=self.temp_dir,  # Ensure command is run in temp directory
                capture_output=True,
                text=True,
                timeout=60
            )
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            if result.returncode == 0:
                return {"success": True, "error": None}
            else:
                return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _Code_Execution(self, project_dir: str) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ["dotnet", "run", "--project", project_dir],
                cwd=self.temp_dir,  # Ensure command is run in temp directory
                capture_output=True,
                text=True,
                timeout=self.lang_config["timeout"]
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
                return {
                    "success": False,
                    "stage": "execution",
                    "error": result.stderr,
                    "error_type": "RuntimeError",
                    "feedback": f"Runtime Error: {result.stderr}"
                }
        except Exception as e:
            return {
                "success": False,
                "stage": "execution",
                "error": str(e),
                "error_type": "ExecutionError",
                "feedback": f"Execution Error: {str(e)}"
            }
    

    # def install_dependencies(self, code: str):
    #     import re
    #     usings = re.findall(r'^\s*using ([\w\.]+);', code, re.MULTILINE)
    #     std_libs = {'System', 'System.Collections', 'System.IO', 'System.Linq', 'System.Text', 'System.Threading', 'System.Net'}
    #     to_install = [pkg for pkg in set(usings) if not any(pkg.startswith(std) for std in std_libs)]
    #     for pkg in to_install:
    #         try:
    #             print(f"Installing C# package: {pkg}")
    #             subprocess.run(["dotnet", "add", self.temp_dir, "package", pkg], check=True)
    #         except Exception as e:
    #             print(f"Failed to install {pkg}: {e}")
    
    
    
    

class TestExecutorFactory:
    @staticmethod
    def create_executor(target_language: TargetLanguage) -> BaseTestExecutor:
        if target_language == TargetLanguage.PYTHON:
            return PythonTestExecutor(target_language)
        elif target_language == TargetLanguage.JAVA:
            return JavaTestExecutor(target_language)
        elif target_language == TargetLanguage.CSHARP:
            return CSharpTestExecutor(target_language)
        else:
            raise ValueError(f"Unsupported language: {target_language}")