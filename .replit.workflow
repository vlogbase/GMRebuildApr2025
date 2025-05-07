run = "python app_workflow.py"
language = "python"
entrypoint = "app_workflow.py"
hidden = [".pythonlibs"]
onBoot = ""

[languages.python.languageServer]
start = ["pylsp"]

[nix]
channel = "stable-22_11"

[env]
VIRTUAL_ENV = "/home/runner/${REPL_SLUG}/venv"
PATH = "${VIRTUAL_ENV}/bin"
PYTHONPATH = "${VIRTUAL_ENV}/lib/python3.11/site-packages"
REPLIT_POETRY_PYPI_REPOSITORY = "https://package-proxy.replit.com/pypi/"
MPLBACKEND = "TkAgg"
POETRY_CACHE_DIR = "${HOME}/${REPL_SLUG}/.cache/pypoetry"

[deployment]
run = ["python", "app_workflow.py"]
deploymentTarget = "cloudrun"
ignorePorts = false