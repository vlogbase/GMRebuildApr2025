[dev]
  pattern = "**/*.py"
  onFileChange = ["workflows/app_workflow.py"]

[test_marketing]
  onBoot = "python workflows/test_marketing.py"
  
[app]
  onBoot = "python app_workflow.py"
  clearOnRestart = false
  restartPolicy = "on-failure"

[job_worker]
  onBoot = "python job_worker_workflow.py"
  clearOnRestart = false
  restartPolicy = "on-failure"