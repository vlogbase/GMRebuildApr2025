run = ["python3", "affiliate_test_workflow.py"]
hidden = ["venv", ".config", "**/__pycache__", "**/.mypy_cache", "**/*.pyc"]
language = "python3"
entrypoint = "affiliate_test_workflow.py"

[nix]
channel = "stable-23_11"

[languages]

[languages.python3]
pattern = "**/*.py"

[languages.python3.languageServer]
start = "pylsp"

[dev]
sslAllowInsecureLocalhost = true