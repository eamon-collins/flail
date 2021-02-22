"""
WSGI config for flail project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os
import threading
import fetch.reddit as reddit

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flail.settings')

#CAUTION: PRIMITIVE THREADING SOLUTION
#starts a thread when the 
# t = threading.Thread(target=reddit.central_reddit_fetch())
# t.setDaemon(True)
# t.start()

application = get_wsgi_application()
