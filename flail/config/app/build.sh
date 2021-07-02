#!/bin/bash

############################################################################
#### These commands are to be run as part of a docker-compose.yml file. ####
#### They are run when the application container is first spun up.      ####
############################################################################

cd flail

# Wait to connect to the postgres DB before continuing. The postgres DB is it's
## own container, alongside this one, built from the same docker-compose.yml file

if [ "$DATABASE" = "postgres" ]
then
  echo "Waiting for postgres..."
  RETRIES=10
  while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
    sleep 0.1
  done
  until PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c 'select 1' > /dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
    echo "Waiting for postgres server, $((RETRIES--)) remaining attempts..."
    sleep 1
  done
  echo "PostgreSQL started"
fi

# Stage the Django application and database
if [ "$FLUSH_DATABASE" = "true" ]
then
  # Clear all data in database
  echo "Flushing Database"
  python manage.py flush --no-input
  # Update database schema to match Django models
  echo "Making Migrations"
  python manage.py makemigrations --no-input
  echo "Migrating Database"
  python manage.py migrate --no-input
  # Configure a super user to first log in with
  echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | python manage.py shell
fi

# Update database schema to match Django models
python manage.py makemigrations --no-input
python manage.py migrate --no-input
# Move static files to designated location (location set in flail/settings.py)
python manage.py collectstatic --no-input
# Upsert default values in database
source config/postgres/build.sh

python startBackend.py &
echo "Started Backend process"

# Start application
# Start up nginx web server
/etc/init.d/nginx start
# Start up application server
uwsgi --socket :8001 --module flail.wsgi --processes 4 --workers 4  --chmod-socket=664 --harakiri=300 --enable-threads --master --single-interpreter

exec "$@"
