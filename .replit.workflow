[default.tasks]

[default.tasks.server]
command = ["python", "run_app.py"]
dependencies = []

[default.tasks.fix-pdf]
command = ["python", "fix_pdf_support.py"]
dependencies = []

[default.tasks.test-pdf]
command = ["python", "test_pdf_handling.py"]
dependencies = []