run = ["python", "test_rag_indicator.py"]
hidden = ["venv", ".config", "**/__pycache__", "**/.mypy_cache", "**/*.pyc"]
onBoot = ["echo hello world"]

[languages.python3]
pattern = "**/*.py"
syntax = "python"

[languages.python3.languageServer]
start = ["pylsp"]

[unitTest]
language = "python3"

[nix]
channel = "stable-22_11"

[env]
PYTHONHASHSEED = "0"
PYTHONPATH = "${PYTHONPATH}:${REPL_HOME}"