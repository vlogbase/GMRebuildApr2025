[workflow]
[workflow.app]
onBoot = "cd '${REPL_HOME}' && python -m flask run --host=0.0.0.0 --port=5000"
run = "cd '${REPL_HOME}' && python -m flask run --host=0.0.0.0 --port=5000"

[workflow.job_worker]
onBoot = "cd '${REPL_HOME}' && python job_worker_workflow.py --workers 2 --queues high,default,low,email,indexing"
run = "cd '${REPL_HOME}' && python job_worker_workflow.py --workers 2 --queues high,default,low,email,indexing"