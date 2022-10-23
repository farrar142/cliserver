celery multi stopwait 2 -A base --pidfile=/var/run/%n.pid --logfile=/var/run/%n.log --loglevel=INFO
celery multi start 2 -A base --pidfile=/var/run/%n.pid --logfile=/var/run/%n.log --loglevel=INFO