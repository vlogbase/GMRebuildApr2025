[nix]
channel = "stable-23_11"

[env]
PYTHONPATH = "/home/runner/${REPL_SLUG}"

[deployment]
run = ["python3", "app_workflow.py"]
deploymentTarget = "cloudrun"

[languages]

[languages.python3]
pattern = "**/*.py"

[languages.python3.languageServer]
start = "pylsp"

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
program = "main.py"
request = "launch"
type = "python"

[packager]
language = "python3"
ignoredPackages = ["unit_tests"]

[packager.features]
enabledForHosting = false
packageSearch = true
guessImports = true

[server]
port = 5000
run = ["python3", "app_workflow.py"]