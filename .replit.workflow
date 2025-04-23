name = "web"
entrypoint = "app_workflow.py"
run = ["python", "app_workflow.py"]
language = "python3"
hidden = ["venv"]

[nix]
channel = "stable-22_11"

[env]
PORT = "5000"
VIRTUAL_ENV = "/home/runner/${REPL_SLUG}/venv"
PATH = "${VIRTUAL_ENV}/bin:/home/runner/${REPL_SLUG}/.config/npm/node_global/bin:${PATH}"

[packager]
language = "python3"
ignoredPackages = ["unit_tests"]

[packager.features]
enabledForHosting = true
packageSearch = true
guessImports = true

[languages.python3]
pattern = "**/*.py"
syntax = "python"

[languages.python3.languageServer]
start = ["pylsp"]

[webview]
icon = "/static/images/favicon.ico"
favicon = "/static/images/favicon.ico"