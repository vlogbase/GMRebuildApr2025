{
  "workflows": {
    "test_affiliate_workflow": {
      "name": "Affiliate System Test",
      "command": "python test_affiliate_workflow.py",
      "restartOn": {
        "files": [
          "test_affiliate_workflow.py",
          "app.py",
          "affiliate_blueprint_fix.py",
          "templates/affiliate/*.html"
        ]
      }
    },
    "app_workflow": {
      "name": "Main Application",
      "command": "python app_workflow.py",
      "restartOn": {
        "files": [
          "app_workflow.py",
          "app.py",
          "affiliate_blueprint_fix.py",
          "templates/**/*.html"
        ]
      }
    }
  }
}