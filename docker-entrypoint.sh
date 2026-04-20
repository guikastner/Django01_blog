#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS_ON_STARTUP:-false}" = "true" ]; then
  python manage.py migrate --noinput
fi

if [ "${CREATE_SUPERUSER_ON_STARTUP:-true}" = "true" ]; then
  python manage.py ensure_superuser
fi

exec "$@"
