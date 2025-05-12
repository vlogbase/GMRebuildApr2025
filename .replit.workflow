run = "python app_workflow.py"
hidden = ["venv", ".config", "**/__pycache__", "**/.mypy_cache", "**/*.pyc"]
entrypoint = "main.py"
language = "python3"

# Specifies which nix channel to use when building the environment.
[nix]
channel = "stable-23_11"

[languages]

[languages.python3]
pattern = "**/*.py"

[languages.python3.languageServer]
start = "pylsp"

[env]
PYTHONPATH = "$PYTHONPATH:${REPL_HOME}"
PATH = "$REPL_HOME/.pythonlibs/bin:$PATH"

# Packager.toml
[packager]
language = "python3"
ignoredPackages = ["unit_tests"]

[packager.features]
enabledForHosting = false
packageSearch = true
guessImports = true

[unitTest]
language = "python3"

[deployment]
run = ["sh", "-c", "python app_workflow.py"]

[auth]
pageEnabled = false
buttonEnabled = false