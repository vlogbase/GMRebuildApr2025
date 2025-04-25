[workflows.flask_app]
onBoot = true
startCommand = ["python", "-m", "flask_app_workflow"]
restartOn = ["flask_app_workflow.py", "app.py", "static/**", "templates/**"]