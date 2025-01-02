import multiprocessing

# Number of worker processes
workers = multiprocessing.cpu_count() * 2 + 1

# Bind address
bind = "0.0.0.0:10000"

# Timeout for worker processes
timeout = 120

# Worker class type
worker_class = "gthread"
threads = 4

# Maximum requests before worker restart
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "moviematch"

# SSL configuration (if needed)
# keyfile = "path/to/keyfile"
# certfile = "path/to/certfile" 