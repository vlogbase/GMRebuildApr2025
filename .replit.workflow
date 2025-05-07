{
  "workflows": {
    "start": {
      "sections": [
        {
          "name": "Start Application",
          "tasks": {
            "run": "python run_app_workflow.py"
          }
        }
      ]
    },
    "app_workflow": {
      "sections": [
        {
          "name": "Run Flask App",
          "tasks": {
            "run": "python app_workflow.py"
          }
        }
      ]
    },
    "fixed_app": {
      "sections": [
        {
          "name": "Run Fixed Flask App",
          "tasks": {
            "run": "python run_fixed_app_workflow.py"
          }
        }
      ]
    }
  }
}