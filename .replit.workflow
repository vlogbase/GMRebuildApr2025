[auth]
[auth.repl]
accessToken = ""

[runner]
initialState = "ready"

[deployment]
deploymentTarget = "cloudrun"
ignorePorts = false
publicDir = "/public"

[dev]
buildCommand = "echo 'no build step'"
startCommand = "python3 app.py"

[affiliate]
buildCommand = "echo 'starting affiliate test workflow'"
startCommand = "python3 affiliate_test_workflow.py"