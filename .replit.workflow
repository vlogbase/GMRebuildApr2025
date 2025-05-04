run = "python -m flask run --host=0.0.0.0 --port=5000"
language = "python3"
entrypoint = "app.py"
hidden = ["venv", ".config", "**/__pycache__", "**/.mypy_cache", "**/*.pyc"]

[nix]
channel = "stable-23_05"

[env]
VIRTUAL_ENV = "/home/runner/${REPL_SLUG}/venv"
PATH = "${VIRTUAL_ENV}/bin"
PYTHONPATH = "$PYTHONPATH:${VIRTUAL_ENV}/lib/python3.10/site-packages:${REPL_HOME}"
PYTHONUNBUFFERED = "1"
DATABASE_URL = "postgres://postgres:postgres@localhost:5432/app"

[gitHubImport]
requiredFiles = [".replit", "replit.nix", ".replit.workflow"]

[packager]
language = "python3"
ignoredPackages = ["unit_tests"]

[packager.features]
packageSearch = true
guessImports = true
enabledForHosting = false

[unitTest]
language = "python3"

[debugger]
support = true

[debugger.interactive]
transport = "localhost:0"
startCommand = ["dap-python", "main.py"]

[debugger.interactive.integratedAdapter]
dapTcpAddress = "localhost:0"

[debugger.interactive.initializeMessage]
command = "initialize"
type = "request"

[debugger.interactive.initializeMessage.arguments]
adapterID = "debugpy"
clientID = "replit"
clientName = "replit.com"
columnsStartAt1 = true
linesStartAt1 = true
locale = "en-us"
pathFormat = "path"
supportsInvalidatedEvent = true
supportsProgressReporting = true
supportsRunInTerminalRequest = true
supportsVariablePaging = true
supportsVariableType = true

[debugger.interactive.launchMessage]
command = "launch"
type = "request"

[debugger.interactive.launchMessage.arguments]
console = "externalTerminal"
cwd = "."
debugOptions = []
program = "./main.py"
request = "launch"
type = "python"

[languages]

[languages.python3]
pattern = "**/*.py"

[languages.python3.languageServer]
start = "pylsp"