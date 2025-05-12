[nix]
channel = "stable-23_05"

[deployment]
run = ["python", "app_workflow.py"]
deploymentTarget = "cloudrun"

[[ports]]
localPort = 5000
externalPort = 80