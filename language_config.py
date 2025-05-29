# language_config.py
from enum import Enum
from typing import Dict, Any

class TargetLanguage(Enum):
    PYTHON = "python"
    JAVA = "java"
    CSHARP = "csharp"

class LanguageConfig:
    def __init__(self):
        self.configs = {
            TargetLanguage.PYTHON: {
                "file_extension": ".py",
                "execution_command": ["python"],
                "compile_command": None,
                "code_block_marker": "```python",
                "test_framework": "assert",
                "package_manager": "pip",
                "allowed_packages": {"textblob", "nltk", "scikit-learn", "pandas", "numpy"},
                "timeout": 30
            },
            TargetLanguage.JAVA: {
                "file_extension": ".java",
                "execution_command": ["java"],
                "compile_command": ["javac"],
                "code_block_marker": "```java",
                "test_framework": "junit",
                "package_manager": "maven",
                "allowed_packages": {"junit", "mockito", "apache-commons"},
                "timeout": 45
            },
            TargetLanguage.CSHARP: {
                "file_extension": ".cs",
                "execution_command": ["dotnet", "run"],
                "compile_command": ["dotnet", "build"],
                "code_block_marker": "```csharp",
                "test_framework": "nunit",
                "package_manager": "nuget",
                "allowed_packages": {"NUnit", "Moq", "Newtonsoft.Json"},
                "timeout": 45
            }
        }

    def get_config(self, language: TargetLanguage) -> Dict[str, Any]:
        return self.configs[language]