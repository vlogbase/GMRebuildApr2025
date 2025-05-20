runs = {
  "flask-app": {
    "name": "Flask App",
    "onStart": "python app.py",
    "port": 5000,
    "restartOn": {
      "files": ["app.py", "**/*.py"],
      "ignore": ["**/__pycache__/**", "*.log"]
    }
  }
}