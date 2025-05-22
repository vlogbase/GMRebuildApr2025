[nix]
channel = "stable-23_05"

[deployment]
deploymentTarget = "cloudrun"
run = ["python3", "app.py"]

[languages.python]
pattern = "**/*.py"
syntax = "python"

[languages.python.languageServer]
start = ["pylsp"]

[unitTest]
language = "python"

[env]
PYTHONHASHSEED = "0"
PYTHONPATH = "/home/runner/${REPL_SLUG}"

[gitHubImport]
requiredFiles = [".replit", "replit.nix", ".replit.workflow"]

[packager]
language = "python3"
ignoredPackages = ["unit_tests"]

[packager.features]
guessImports = true
enabledForHosting = false

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

[interpreter]
command = ["python3", "-u"]

[auth]
pageEnabled = false
buttonEnabled = false

[processes]
paypal_update = ["python", "paypal_update_workflow.py"]
app = ["python", "app.py"]