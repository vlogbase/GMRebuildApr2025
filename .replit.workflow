[Start application]
priority = 50
autoWatch = false
showConsoleLogs = true
shellCmdPre = ""
shellCmdPost = ""
autoRun = false
isModule = false

[Start application.commands]
restartable = true
isVisible = true
supportShell = false
isBackspace = false
isCtrlc = false
isKeyStrokes = false
cmd = [
  "gunicorn", 
  "main:app", 
  "-k", "gevent", 
  "-w", "4", 
  "--timeout", "300", 
  "--bind", "0.0.0.0:5000", 
  "--reuse-port", 
  "--reload"
]