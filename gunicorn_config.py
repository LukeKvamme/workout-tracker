bind = "0.0.0.0:8050"
workers = 2
worker_class = "sync"
timeout = 120

accesslog = "-"
errorlog = "-"
loglevel = "info"

proc_name = "workout-tracker"

daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None


max_requests = 1000
max_requests_jitter = 50