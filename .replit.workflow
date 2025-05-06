[run_button_mode]
terminal_workdir = "/"

[run_button_workflow]
name = "GloriaMundo Chat Application"
description = "Run the GloriaMundo Chat Application with the affiliate system"
modules = ["python-3.11", "postgresql-16"]
terminalTitle = "GloriaMundo Chat"
isSwitchNode = true
nodes = ["Run DB Migrations", "Run App Server"]

[Run DB Migrations]
workdir = "/"
command = ["python", "migrations.py"]
start = "Run App Server"
disableConfidentialityWarning = true

[Run App Server]
workdir = "/"
command = ["gunicorn", "main:app", "-k", "gevent", "-w", "4", "--timeout", "300", "--bind", "0.0.0.0:5000", "--reuse-port", "--reload"]
terminalTitle = "Flask Server"
disableConfidentialityWarning = true