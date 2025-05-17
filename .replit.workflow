workflows:
  model_fallback_test:
    run: python model_fallback_test_workflow.py
    persistent: true
  
  app:
    run: python app.py
    persistent: true