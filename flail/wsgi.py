"""
WSGI config for flail project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os
import threading
from multiprocessing import Process, Lock
import fetch.reddit as reddit

from django.core.wsgi import get_wsgi_application
from django import db

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flail.settings')


def fetch_thread():
	reddit.central_reddit_fetch()
	#CAUTION: PRIMITIVE THREADING SOLUTION
	#starts a thread when the 
	# t = threading.Thread(target=reddit.central_reddit_fetch())
	# t.setDaemon(True)
	# t.start()

def server_thread():
	application = get_wsgi_application()


db.connections.close_all()

databaseLock = Lock()
pFetch = Process(target=fetch_thread)
pServer = Process(target=server_thread)

pFetch.start()
application = get_wsgi_application()
#pServer.start()