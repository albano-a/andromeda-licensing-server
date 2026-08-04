#!/bin/sh
set -eu

if [ "${CREATE_DATABASE_ON_STARTUP:-true}" = "true" ]; then
  python /app/scripts/create_database.py
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000