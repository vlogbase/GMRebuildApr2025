[workflows.flask_app]
onBoot = true
startCommand = ["python", "flask_app_workflow.py"]
restartOn = ["flask_app_workflow.py", "app.py", "static/**", "templates/**"]