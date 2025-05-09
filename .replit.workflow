{
  "runners": [
    {
      "name": "Admin Dashboard",
      "language": "python3",
      "id": "admin_dashboard",
      "directory": "/",
      "start": "python admin_app_workflow.py",
      "restartOn": {
        "files": ["admin_app_workflow.py", "affiliate.py", "auth_utils.py", "billing.py", "static/js/admin.js", "static/js/admin-dashboard.js", "static/css/admin-dashboard.css"]
      },
      "public": true
    }
  ]
}