[app]
run = ["python", "app_workflow.py"]
language = "python3"

[fix_schema]
run = ["python", "fix_affiliate_schema.py"]
language = "python3"

[flask_app]
run = ["python", "app.py"]
language = "python3"

[run_openrouter_migrations]
run = ["python", "run_openrouter_migrations.py"]
language = "python3"