#!/bin/bash
# Startup script for Railway deployment
# Properly expands PORT environment variable

gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:${PORT:-5000} server.app:app
