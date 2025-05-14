{
  "runs": {
    "mobile_ui_test": {
      "command": "python workflows/mobile_ui_test.py",
      "description": "Run the Flask application to test mobile UI improvements",
      "runOnStart": false
    },
    "app_workflow": {
      "command": "python app_workflow.py",
      "description": "Run the standard app workflow",
      "runOnStart": false
    }
  }
}