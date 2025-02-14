#!/bin/bash
set -e

echo "Starting server..."
exec gunicorn \
    --worker-class eventlet \
    -w 1 \
    --bind 0.0.0.0:$PORT \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    'server:app' 