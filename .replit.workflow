[workflow.server]
run = "python flask_workflow.py"
interpreter = ["python", "-m"]
stdout = "server"
interactive = true
onBoot = "python -c 'from flask_workflow import run; run()'"