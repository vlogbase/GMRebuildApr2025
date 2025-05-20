run = "python app.py"
language = "python"
entrypoint = "app.py"
hidden = ["__pycache__", "*.pyc", "*.pyo", "*.pyd", ".Python", "env", "venv", ".env", ".venv"]
modules = ["python-3.10:v18-20230807-322e88b"]

[env]
PYTHONPATH = "$PYTHONPATH:."
PYTHONUNBUFFERED = "1"
FLASK_ENV = "development"
FLASK_DEBUG = "1"

[nix]
channel = "stable-23_05"

[gitHubImport]
requiredFiles = [".replit", "replit.nix"]

[deployment]
run = ["sh", "-c", "python app.py"]
deploymentTarget = "cloudrun"
ignorePorts = false