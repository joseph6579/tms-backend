#!/bin/sh

# Apply database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Prepare gunicorn log files
mkdir -p /deployment/logs/gunicorn/

touch /deployment/logs/gunicorn/access.log
touch /deployment/logs/gunicorn/error.log
# Start Gunicorn processes
echo Starting Gunicorn.
exec gunicorn tms.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --log-level=info \
    --access-logfile=/deployment/logs/gunicorn/access.log \
    --error-logfile=/deployment/logs/gunicorn/error.log \
    --capture-output \
    "$@"