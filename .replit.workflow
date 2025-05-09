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
    },
    {
      "name": "Admin Test",
      "language": "python3",
      "id": "admin_test_workflow",
      "directory": "/",
      "start": "python admin_test_workflow.py",
      "restartOn": {
        "files": ["admin_test_workflow.py", "debug_admin_tab.py", "templates/account.html", "templates/affiliate/admin_tab.html"]
      },
      "public": true
    },
    {
      "name": "Test Admin Tab",
      "language": "python3",
      "id": "test_admin",
      "directory": "/",
      "start": "python test_admin_workflow.py",
      "restartOn": {
        "files": ["test_admin_workflow.py", "templates/account.html", "templates/affiliate/admin_tab.html", "static/js/admin.js", "static/js/admin-dashboard.js", "static/js/account_clean.js"]
      },
      "public": true
    },
    {
      "name": "Debug Admin Visibility",
      "language": "python3",
      "id": "debug_admin_visibility",
      "directory": "/",
      "start": "python debug_admin_visibility_workflow.py",
      "restartOn": {
        "files": ["debug_admin_visibility_workflow.py", "debug_admin_visibility.py", "templates/account.html", "templates/affiliate/admin_tab.html", "static/js/admin.js"]
      },
      "public": true
    }
  ]
}