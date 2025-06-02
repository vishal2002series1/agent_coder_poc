import subprocess
import os
import tempfile
import shutil
import ssl


def test_maven_dependency_download():
    """
    Test if we can download Java dependencies using Maven in subprocess
    """
    print("=== Testing Maven Dependency Download ===\n")

    # Define the explicit path to Maven executable for Windows
    # This path comes directly from your 'mvn -v' output:
    # Maven home: C:\ProgramData\chocolatey\lib\maven\apache-maven-3.9.9
    # The executable is mvn.cmd within its 'bin' directory.
    maven_home = r"C:\ProgramData\chocolatey\lib\maven\apache-maven-3.9.9"
    maven_command = os.path.join(maven_home, "bin", "mvn.cmd")

    # Verify if the explicit path exists
    if not os.path.exists(maven_command):
        print(f"✗ Error: Maven executable not found at specified path: {maven_command}")
        print("Please ensure the path to your Maven installation is correct.")
        return False

    # Create a temporary directory for our test
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Working in temporary directory: {temp_dir}")

        # Create a minimal pom.xml file
        pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.test</groupId>
    <artifactId>dependency-test</artifactId>
    <version>1.0.0</version>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-lang3</artifactId>
            <version>3.12.0</version>
        </dependency>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
        </dependency>
    </dependencies>
</project>"""

        # Write pom.xml to temp directory
        pom_path = os.path.join(temp_dir, "pom.xml")
        with open(pom_path, 'w') as f:
            f.write(pom_content)
        print("✓ Created pom.xml")

        # Test 1: Check if Maven is available
        try:
            # Use the explicitly defined maven_command
            result = subprocess.run([maven_command, '--version'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✓ Maven is available")
                print(f"Maven version: {result.stdout.split()[2]}")
            else:
                print(f"✗ Maven command failed with return code {result.returncode}")
                print(f"Error output: {result.stderr}")
                return False
        except FileNotFoundError:
            print(f"✗ Maven not found at specified path: {maven_command}")
            print("Please ensure the Maven executable exists at this location.")
            return False
        except subprocess.TimeoutExpired:
            print("✗ Maven version check timed out")
            return False
        except Exception as e:
            print(f"✗ An unexpected error occurred during Maven version check: {str(e)}")
            return False


        # Test 2: Download dependencies
        print("\n--- Downloading dependencies ---")
        try:
            # Use the explicitly defined maven_command
            result = subprocess.run([
                maven_command, 'dependency:copy-dependencies',
                '-DoutputDirectory=lib',
                '-DincludeScope=compile'
            ], cwd=temp_dir, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                print("✓ Maven dependency download completed")

                # Check if lib directory was created and contains JARs
                lib_dir = os.path.join(temp_dir, "lib")
                if os.path.exists(lib_dir):
                    jar_files = [f for f in os.listdir(lib_dir) if f.endswith('.jar')]
                    print(f"✓ Found {len(jar_files)} JAR files:")
                    for jar in jar_files:
                        print(f"  - {jar}")

                    # Check for specific dependencies
                    commons_lang = any('commons-lang3' in jar for jar in jar_files)
                    junit_jar = any('junit' in jar for jar in jar_files)

                    if commons_lang:
                        print("✓ Apache Commons Lang3 downloaded successfully")
                    else:
                        print("✗ Apache Commons Lang3 not found")

                    if junit_jar:
                        print("✓ JUnit downloaded successfully")
                    else:
                        print("✗ JUnit not found")

                    return commons_lang and junit_jar
                else:
                    print("✗ lib directory not created")
                    return False
            else:
                print("✗ Maven dependency download failed")
                print(f"Error output: {result.stderr}")
                print(f"Standard output: {result.stdout}") # Add this to see more details
                return False

        except subprocess.TimeoutExpired:
            print("✗ Maven dependency download timed out")
            return False
        except Exception as e:
            print(f"✗ Error during Maven execution: {str(e)}")
            return False

def test_direct_jar_download():
    """
    Alternative test: Direct JAR download from Maven Central
    """
    print("\n=== Testing Direct JAR Download ===\n")

    import urllib.request

    with tempfile.TemporaryDirectory() as temp_dir:
        jar_url = "https://repo1.maven.org/maven2/org/apache/commons/commons-lang3/3.12.0/commons-lang3-3.12.0.jar"
        jar_path = os.path.join(temp_dir, "commons-lang3-3.12.0.jar")

        try:
            print(f"Downloading from: {jar_url}")
            urllib.request.urlretrieve(jar_url, jar_path)

            if os.path.exists(jar_path):
                file_size = os.path.getsize(jar_path)
                print(f"✓ JAR downloaded successfully ({file_size} bytes)")
                return True
            else:
                print("✗ JAR file not found after download")
                return False

        except Exception as e:
            print(f"✗ Direct download failed: {str(e)}")
            return False

if __name__ == "__main__":
    # ssl._create_default_https_context = ssl._create_unverified_context
    print("Testing Java dependency download capabilities...\n")

    # Test Maven approach
    maven_success = test_maven_dependency_download()

    # Test direct download approach
    direct_success = test_direct_jar_download()

    print("\n=== SUMMARY ===")
    print(f"Maven approach: {'✓ SUCCESS' if maven_success else '✗ FAILED'}")
    print(f"Direct download: {'✓ SUCCESS' if direct_success else '✗ FAILED'}")

    if maven_success:
        print("\nRecommendation: Use Maven subprocess for dependency management")
    elif direct_success:
        print("\nRecommendation: Use direct JAR download (no transitive dependencies)")
    else:
        print("\nRecommendation: Consider pre-installing dependencies or using a different approach")