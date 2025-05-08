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
            "run": "python workflows/fixed_app_workflow.py"
          }
        }
      ]
    },
    "rag_fixed": {
      "sections": [
        {
          "name": "Run RAG Fixed Flask App",
          "tasks": {
            "run": "python rag_fixed_app_workflow.py"
          }
        }
      ]
    },
    "rag_fixed_app_workflow": {
      "sections": [
        {
          "name": "Run RAG Fixed Flask App (Alternative)",
          "tasks": {
            "run": "python rag_fixed_app_workflow.py"
          }
        }
      ]
    },
    "test_ui": {
      "sections": [
        {
          "name": "Test UI Enhancements",
          "tasks": {
            "run": "python test_ui_workflow.py"
          }
        }
      ]
    }
  }
}