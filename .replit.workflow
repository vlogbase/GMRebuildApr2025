workflows:
  run_app:
    run: python app_workflow.py
    onBoot: true
    environment:
      PORT: 5000
    restartOn:
      changes: ["app.py", "templates/**", "static/**"]