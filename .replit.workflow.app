run = "python app.py"
language = "python"
entrypoint = "app.py"
guessImports = true

[nix]
channel = "stable-22_11"

[env]
PYTHONPATH = "$PYTHONPATH:."
PYTHONUNBUFFERED = "1"
FLASK_ENV = "development"
FLASK_DEBUG = "1"

[deployment]
deploymentTarget = "cloudrun"