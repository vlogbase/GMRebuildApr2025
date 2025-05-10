[editor]
    defaultViewType = "preview"

[permission]
    private = true
    persistPath = false

[run]
    ignorePersist = true
    command = "python app_document_indicator_workflow.py"

[deployment]
    deploymentTarget = "cloudrun"
    publicDir = "/"
    ignorePaths = []
    build = ""
    run = "python run.py"

[languages.python]
    pattern = "**/*.py"
    syntax = "python"

[languages.python.languageServer]
    start = ["pylsp"]

[languages.json]
    pattern = "**/*.json"
    syntax = "json"

[languages.json.languageServer]
    start = ["vscode-json-language-server", "--stdio"]

[languages.html]
    pattern = "**/*.html"
    syntax = "html"

[languages.html.languageServer]
    start = ["vscode-html-language-server", "--stdio"]

[languages.css]
    pattern = "**/*.css"
    syntax = "css"

[languages.css.languageServer]
    start = ["vscode-css-language-server", "--stdio"]

[languages.javascript]
    pattern = "**/*.js"
    syntax = "javascript"

[languages.javascript.languageServer]
    start = ["typescript-language-server", "--stdio"]
    
[[hints]]
    regex = "HINT1"
    message = "First message"

[nix]
    channel = "stable-22_11"

[env]
    VIRTUAL_ENV = "/home/runner/${REPL_SLUG}/venv"
    PATH = "${VIRTUAL_ENV}/bin"
    PYTHONPATH = "$PYTHONHOME/lib/python3.10:${VIRTUAL_ENV}/lib/python3.10/site-packages"
    REPLIT_DISABLE_LEGACY_PYTHON_30M = "1"
    PYTHONUNBUFFERED = "1"

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
            command = "attach"
            type = "request"

            [debugger.interactive.launchMessage.arguments]
                logging = {}

[interpreter]
    command = ["python3", "-u"]

[auth]
    pageEnabled = true
    buttonEnabled = true