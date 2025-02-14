#!/bin/bash
set -e

echo "Starting server..."
exec gunicorn \
    --worker-class gevent \
    --worker-connections 1000 \
    --timeout 120 \
    -w 1 \
    --bind 0.0.0.0:$PORT \
    --log-level debug \
    --access-logfile - \
    --error-logfile - \
    'server:app' 