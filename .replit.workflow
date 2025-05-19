[app_workflow]
id = "app_workflow"
name = "App Server"
entrypoint = "python main.py"
language = "python3"
run_command = "python main.py"
run_args = ""
on_file_change = "restart"
persistent = true
persistent_timeout = 20
env_from_repo_secrets = ["REDIS_HOST", "AZURE_STORAGE_CONNECTION_STRING", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "OPENROUTER_API_KEY"]