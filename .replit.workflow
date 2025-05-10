run = "python main.py"
language = "python3"
hidden = false
webview = "website"
onBoot = ""
interpreter = "/nix/store/2vm88xw7513h9pyjyafw32cjkwmqim1x-python3-3.11.9/bin/python3.11"
entrypoint = "main.py"

[nix]
channel = "stable-23_11"

[deployment]
run = ["sh", "-c", "python main.py"]
deploymentTarget = "cloudrun"