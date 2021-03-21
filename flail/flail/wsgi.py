"""
WSGI config for flail project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

#import django
#django.setup()
 
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flail.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import threading
from multiprocessing import Process, Lock
import fetch.reddit as reddit
import analyze.sentiment as sentiment

from django import db

def fetch_thread():
	reddit.central_reddit_fetch()

def analyze_queue_thread():
	sentiment.central_queue_analyze()

def prepare_graphs_thread():
	sentiment.prepare_all_graphs()

#This works so far. Investigating a mysql or postgres database
#solution would be a good addition to minimize multiple db 
#connections causing trouble. Postgres is #1 option
#maybe also do a stress test/consistency check to make sure no indeterminacies?


#db.connections.close_all()


# databaseLock = Lock()
# pFetch = Process(target=fetch_thread)
# pAnalyze = Process(target=analyze_queue_thread)
# pGraph = Process(target=prepare_graphs_thread)

# pFetch.start()
# pAnalyze.start() 
# pGraph.start()