from setuptools import setup

setup(
    name='flail',
	version='1.1',
	description='flail',
	author='Eamon Collins',
	author_email='eamonacollins@gmail.com',
	packages=['flail'],
    url='https://github.com/eamon-collins/flail',
	install_requires=['django==3.0.5','django-crispy-forms==1.9.0','django-extensions==2.2.9',
                          'pandas','requests==2.23.0',
                          'uwsgi==2.0.18', 'jupyter==1.0.0', 'ipython==7.14.0', 'psycopg2-binary',
                          'html5lib==1.1', 'prettyprint==0.1.5', 'celery',
                          'response==0.4.0', 'flask==1.1.2', 'django-apscheduler', 'apscheduler',
                          'djangorestframework', 'SQLAlchemy', 'django-redis', 'django-celery-results',
                          'django-allauth', 'setuptools_rust', 'python-dotenv', 'django-contrib-comments',
                          'matplotlib', 'numpy', 'vaderSentiment', 'praw'
                         ]
)