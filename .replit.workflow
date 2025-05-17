run = "python app_workflow.py"
entrypoint = "app_workflow.py"
hidden = false
onBoot = false

[env]
PYTHONUNBUFFERED = "1"

[nix]
channel = "stable-22_11"

[deployment]
run = ["sh", "-c", "cd ${REPL_HOME} && python app_workflow.py"]
