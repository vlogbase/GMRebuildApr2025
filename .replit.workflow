run = [
  "python", "startup_test_workflow.py"
]

entrypoint = "startup_test_workflow.py"

language = "python3"

[env]
VIRTUAL_ENV = "/home/runner/${REPL_SLUG}/venv"
PATH = "${VIRTUAL_ENV}/bin"
PYTHONPATH = "$PYTHONHOME/lib/python3.10:${VIRTUAL_ENV}/lib/python3.10/site-packages"

[nix]
channel = "stable-22_11"

[deployment]
run = ["python", "startup_test_workflow.py"]
deploymentTarget = "cloudrun"