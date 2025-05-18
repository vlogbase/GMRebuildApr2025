[dev]
  pattern = "**/*.py"
  onFileChange = ["workflows/app_workflow.py"]

[test_marketing]
  onBoot = "python workflows/test_marketing.py"
  
[app]
  onBoot = "python app.py"