run = ["python", "run.py"]
language = "python3"
entrypoint = "app.py"
hidden = ["venv", ".config", "**/__pycache__", "**/.pytest_cache", "**/*.pyc"]

# Specifies which ports to expose, using the format "public:private". You can only expose a port if the private port is already listed in a `[ports]` section. Currently, exposed ports are only supported for blank repls.

[nix]
channel = "stable-22_11"

[env]
VIRTUAL_ENV = "${REPL_HOME}/venv"
PATH = "${VIRTUAL_ENV}/bin"
PYTHONPATH = "$PYTHONPATH:${REPL_HOME}"
REPLIT_POETRY_PYPI_REPOSITORY = "https://package-proxy.replit.com/pypi/"
MPLBACKEND = "TkAgg"
PYTHONUNBUFFERED = "1"

[packager]
language = "python3"

[packager.features]
enabledForHosting = false
packageSearch = true
guessImports = true

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
command = "attach"
type = "request"

[debugger.interactive.launchMessage.arguments]
logging = {}

[unitTest]
language = "python3"

[auth]
pageEnabled = true
buttonEnabled = false