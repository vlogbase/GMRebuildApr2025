[workflows.gm_admin_workflow]
onBoot = false
clearOnRerun = true
restartOn = {}
name = "GM Admin Dashboard"
startCommand = ["python", "workflows/gm_admin_workflow.py"]

[workflows.gm_admin_test]
onBoot = false
clearOnRerun = true
restartOn = {}
name = "Test Admin Dashboard"
startCommand = ["python", "gm_admin_test.py"]