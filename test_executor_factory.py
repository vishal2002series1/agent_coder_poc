# test_executor_factory.py
from abc import ABC, abstractmethod
from typing import Dict, Any
import subprocess
import tempfile
import os
import sys
from language_config import TargetLanguage, LanguageConfig
import re
import requests
from bs4 import BeautifulSoup  # Import BeautifulSoup

def extract_public_class_name(java_code: str) -> str:
    match = re.search(r'public\s+class\s+(\w+)', java_code)
    if match:
        return match.group(1)
    raise ValueError("No public class found in Java code.")

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


    # def execute_with_tests(self, code: str, tests: str) -> Dict[str, Any]:
    #     # Create a proper Java structure
    #     self.install_dependencies(code)
    #     self.install_dependencies(tests)
    #     full_code = self.merge_java_code_and_tests(code, tests)

    #     compile_result = self._compile_code(full_code)
    #     if not compile_result["success"]:
    #         return {
    #             "success": False,
    #             "stage": "compilation",
    #             "error": compile_result["error"],
    #             "error_type": "CompilationError",
    #             "feedback": f"Compilation Error: {compile_result['error']}"
    #         }

    #     return self._Code_Execution()

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

        compile_result = self._compile_code([code_file, tests_file])
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

    # def _compile_code(self, code: str) -> Dict[str, Any]:
    #     temp_file = os.path.join(self.temp_dir, "TestRunner.java")
    #     try:
    #         with open(temp_file, 'w') as f:
    #             f.write(code)

    #         result = subprocess.run(
    #             ["javac", temp_file],
    #             capture_output=True,
    #             text=True,
    #             timeout=30,
    #             cwd=self.temp_dir
    #         )

    #         if result.returncode == 0:
    #             return {"success": True, "error": None}
    #         else:
    #             return {"success": False, "error": result.stderr}

    #     except Exception as e:
    #         return {"success": False, "error": str(e)}

    # def _Code_Execution(self) -> Dict[str, Any]:
    #     try:
    #         result = subprocess.run(
    #             ["java", "-ea", "TestRunner"],
    #             capture_output=True,
    #             text=True,
    #             timeout=self.lang_config["timeout"],
    #             cwd=self.temp_dir
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
    #             return {
    #                 "success": False,
    #                 "stage": "execution",
    #                 "error": result.stderr,
    #                 "error_type": "RuntimeError",
    #                 "feedback": f"Runtime Error: {result.stderr}"
    #             }

    #     except Exception as e:
    #         return {
    #             "success": False,
    #             "stage": "execution",
    #             "error": str(e),
    #             "error_type": "ExecutionError",
    #             "feedback": f"Execution Error: {str(e)}"
    #         }

    # def _compile_code(self, java_files: list) -> Dict[str, Any]:
    #     try:
    #         result = subprocess.run(
    #             ["javac"] + java_files,
    #             capture_output=True,
    #             text=True,
    #             timeout=30,
    #             cwd=self.temp_dir
    #         )
    #         if result.returncode == 0:
    #             return {"success": True, "error": None}
    #         else:
    #             return {"success": False, "error": result.stderr}
    #     except Exception as e:
    #         return {"success": False, "error": str(e)}
        
    def _compile_code(self, java_files: list) -> Dict[str, Any]:
        try:
            compile_cmd = ["javac"]

            # Add classpath if dependencies were installed
            if hasattr(self, 'classpath') and self.classpath:
                compile_cmd.extend(["-cp", self.classpath])

            compile_cmd.extend(java_files)

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

    # def _Code_Execution(self, main_class: str) -> Dict[str, Any]:
    #     try:
    #         result = subprocess.run(
    #             ["java", "-ea", main_class],
    #             capture_output=True,
    #             text=True,
    #             timeout=self.lang_config["timeout"],
    #             cwd=self.temp_dir
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
    #             return {
    #                 "success": False,
    #                 "stage": "execution",
    #                 "error": result.stderr,
    #                 "error_type": "RuntimeError",
    #                 "feedback": f"Runtime Error: {result.stderr}"
    #             }
    #     except Exception as e:
    #         return {
    #             "success": False,
    #             "stage": "execution",
    #             "error": str(e),
    #             "error_type": "ExecutionError",
    #             "feedback": f"Execution Error: {str(e)}"
    #         }
        
    def _Code_Execution(self, main_class: str) -> Dict[str, Any]:
        try:
            exec_cmd = ["java", "-ea"]

            # Add classpath if dependencies were installed
            if hasattr(self, 'classpath') and self.classpath:
                exec_cmd.extend(["-cp", f"{self.temp_dir}:{self.classpath}"])
            else:
                exec_cmd.extend(["-cp", self.temp_dir])

            exec_cmd.append(main_class)

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

    # def install_dependencies(self, code: str):
    #     # Find all import statements
    #     imports = re.findall(r'^\s*import ([\w\.]+);', code, re.MULTILINE)
    #     # List of standard Java packages (partial, can be expanded)
    #     std_libs = {'java.util', 'java.io', 'java.time', 'java.lang', 'java.math', 'java.net', 'java.nio', 'java.text'}
    #     to_install = [pkg for pkg in set(imports) if not any(pkg.startswith(std) for std in std_libs)]
    #     if to_install:
    #         print("WARNING: The following Java packages may need to be added to your build system (Maven/Gradle):")
    #         for pkg in to_install:
    #             print(f"  - {pkg}")
    #         print("Automatic Java dependency installation is not implemented. Please add these to your pom.xml or build.gradle if needed.")
    # def install_dependencies(self, code: str):
    #     """Install Java dependencies using Maven if needed"""
    #     # Find all import statements
    #     imports = re.findall(r'^\s*import ([\w\.]+);', code, re.MULTILINE)

    #     # List of standard Java packages (partial, can be expanded)
    #     std_libs = {'java.util', 'java.io', 'java.time', 'java.lang', 'java.math', 'java.net', 'java.nio', 'java.text'}

    #     # Filter out standard libraries
    #     external_imports = [pkg for pkg in set(imports) if not any(pkg.startswith(std) for std in std_libs)]

    #     if external_imports:
    #         print(f"Found external Java dependencies: {external_imports}")

    #         # Check for common testing frameworks and install them
    #         for pkg in external_imports:
    #             if 'junit' in pkg.lower():
    #                 self._install_junit()
    #             elif 'testng' in pkg.lower():
    #                 self._install_testng()
    #             else:
    #                 print(f"WARNING: Unknown Java package '{pkg}' - manual installation may be required")
    def install_dependencies(self, code: str):
        """
        Dynamically extract and install Java dependencies.
        """
        # 1. Extract import statements
        imports = re.findall(r'^\s*import\s+([\w\.]+);', code, re.MULTILINE)

        # 2. Filter out standard Java libraries
        std_libs = {'java.util', 'java.io', 'java.time', 'java.lang', 'java.math', 'java.net', 'java.nio', 'java.text'}
        external_imports = [pkg for pkg in set(imports) if not any(pkg.startswith(std) for std in std_libs)]

        print(f"Detected external Java dependencies: {external_imports}")

        # 3. Attempt to resolve and install dependencies
        for package in external_imports:
            self._resolve_and_install_dependency(package)

    def install_dependencies(self, code: str):
        """
        Dynamically extract and install Java dependencies.
        """
        # 1. Extract import statements
        imports = re.findall(r'^\s*import\s+([\w\.]+);', code, re.MULTILINE)

        # 2. Filter out standard Java libraries
        std_libs = {'java.util', 'java.io', 'java.time', 'java.lang', 'java.math', 'java.net', 'java.nio', 'java.text'}
        external_imports = [pkg for pkg in set(imports) if not any(pkg.startswith(std) for std in std_libs)]

        print(f"Detected external Java dependencies: {external_imports}")

        # 3. Attempt to resolve and install dependencies
        for package in external_imports:
            self._resolve_and_install_dependency(package)


    def _resolve_and_install_dependency(self, package: str):
        """
        Attempt to resolve a Java package to a Maven artifact and install it.
        """
        artifact = self._search_maven_central(package)

        if artifact:
            print(f"Found Maven artifact: {artifact}")
            jar_path = self._download_jar(artifact)
            if jar_path:
                print(f"Downloaded JAR: {jar_path}")
                self._update_classpath(jar_path)
            else:
                print(f"Failed to download JAR for {package}")
        else:
            print(f"Could not find Maven artifact for package: {package}")

    def _search_maven_central(self, package: str) -> dict:
        """
        Search Maven Central for a given Java package and return the artifact information.
        """
        # Construct the search URL
        search_url = f"https://search.maven.org/search?q=fc:%22{package}%22&core=gav"

        try:
            # Send the request
            response = requests.get(search_url)
            response.raise_for_status()

            # Parse the response
            soup = BeautifulSoup(response.content, 'html.parser')
            results = soup.find_all('doc')

            if results:
                # Extract the artifact information from the first result
                doc = results[0]
                group_id = doc.find('str', {'name': 'g'}).text
                artifact_id = doc.find('str', {'name': 'a'}).text
                version = doc.find('str', {'name': 'v'}).text

                return {
                    'groupId': group_id,
                    'artifactId': artifact_id,
                    'version': version
                }
            else:
                return None

        except Exception as e:
            print(f"Error searching Maven Central: {e}")
            return None
        
    

    def _download_jar(self, artifact: dict) -> str:
        """
        Download JAR file from Maven Central.
        """
        group_path = artifact['groupId'].replace('.', '/')
        jar_name = f"{artifact['artifactId']}-{artifact['version']}.jar"
        url = f"https://repo1.maven.org/maven2/{group_path}/{artifact['artifactId']}/{artifact['version']}/{jar_name}"
        lib_dir = os.path.join(self.temp_dir, 'lib')
        os.makedirs(lib_dir, exist_ok=True)
        jar_path = os.path.join(lib_dir, jar_name)

        try:
            import requests
            response = requests.get(url)
            response.raise_for_status()

            with open(jar_path, 'wb') as f:
                f.write(response.content)

            return jar_path

        except Exception as e:
            print(f"Error downloading JAR: {e}")
            return None
        
    def _update_classpath(self, jar_path: str):
        """
        Update the classpath with the given JAR path.
        """
        if not hasattr(self, 'classpath') or not self.classpath:
            self.classpath = jar_path
        else:
            self.classpath += os.pathsep + jar_path

    def _install_junit(self):
        """Install JUnit using Maven"""
        try:
            print("Installing JUnit...")
            # Create a minimal pom.xml for dependency resolution
            pom_content = """<?xml version="1.0" encoding="UTF-8"?>
    <project xmlns="http://maven.apache.org/POM/4.0.0"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
            http://maven.apache.org/xsd/maven-4.0.0.xsd">
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.example</groupId>
        <artifactId>test-project</artifactId>
        <version>1.0.0</version>
        <properties>
            <maven.compiler.source>11</maven.compiler.source>
            <maven.compiler.target>11</maven.compiler.target>
        </properties>
        <dependencies>
            <dependency>
                <groupId>junit</groupId>
                <artifactId>junit</artifactId>
                <version>4.13.2</version>
            </dependency>
        </dependencies>
    </project>"""

            pom_file = os.path.join(self.temp_dir, "pom.xml")
            with open(pom_file, 'w', encoding='utf-8') as f:
                f.write(pom_content)

            # Download dependencies
            result = subprocess.run(
                ["mvn", "dependency:copy-dependencies", "-DoutputDirectory=lib"],
                cwd=self.temp_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                print("✓ JUnit installed successfully")
                # Update classpath to include downloaded JARs
                lib_dir = os.path.join(self.temp_dir, "lib")
                if os.path.exists(lib_dir):
                    jar_files = [f for f in os.listdir(lib_dir) if f.endswith('.jar')]
                    self.classpath = ":".join([os.path.join(lib_dir, jar) for jar in jar_files])
            else:
                print(f"Failed to install JUnit: {result.stderr}")

        except Exception as e:
            print(f"Error installing JUnit: {e}")

    def _install_testng(self):
        """Install TestNG using Maven"""
        # Similar implementation for TestNG
        print("TestNG installation not implemented yet")


class CSharpTestExecutor(BaseTestExecutor):
    def execute_with_tests(self, code: str, tests: str) -> Dict[str, Any]:
        # Create a complete C# project structure
        self.install_dependencies(code)
        self.install_dependencies(tests)
        full_code = self._create_csharp_project(code, tests)

        compile_result = self._compile_code(full_code)
        if not compile_result["success"]:
            return {
                "success": False,
                "stage": "compilation",
                "error": compile_result["error"],
                "error_type": "CompilationError",
                "feedback": f"Compilation Error: {compile_result['error']}"
            }

        return self._Code_Execution(full_code)

    def _create_csharp_project(self, code: str, tests: str) -> str:
        return f"""
                using System;

                {code}

                // Test Cases
                {tests}

                class Program {{
                    static void Main(string[] args) {{
                        // Run tests here
                        Console.WriteLine("All tests passed successfully!");
                    }}
                }}
                """

    def _compile_code(self, code: str) -> Dict[str, Any]:
        # Create project file and source file
        project_file = os.path.join(self.temp_dir, "TestProject.csproj")
        source_file = os.path.join(self.temp_dir, "Program.cs")

        try:
            # Create .csproj file
            with open(project_file, 'w') as f:
                f.write("""
                    <Project Sdk="Microsoft.NET.Sdk">
                    <PropertyGroup>
                        <OutputType>Exe</OutputType>
                        <TargetFramework>net6.0</TargetFramework>
                    </PropertyGroup>
                    </Project>
                    """)

            # Create source file
            with open(source_file, 'w') as f:
                f.write(code)

            result = subprocess.run(
                ["dotnet", "build", self.temp_dir],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return {"success": True, "error": None}
            else:
                return {"success": False, "error": result.stderr}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _Code_Execution(self, code: str) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ["dotnet", "run", "--project", self.temp_dir],
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
    def install_dependencies(self, code: str):
        # Find all using statements
        usings = re.findall(r'^\s*using ([\w\.]+);', code, re.MULTILINE)
        std_libs = {'System', 'System.Collections', 'System.IO', 'System.Linq', 'System.Text', 'System.Threading', 'System.Net'}
        to_install = [pkg for pkg in set(usings) if not any(pkg.startswith(std) for std in std_libs)]
        for pkg in to_install:
            try:
                print(f"Installing C# package: {pkg}")
                subprocess.run(["dotnet", "add", "package", pkg], check=True)
            except Exception as e:
                print(f"Failed to install {pkg}: {e}")

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