#!/bin/sh
set -e

python - <<'PY'
import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
while s.connect_ex(("mysql", 3306)):
    print("Waiting for MySQL...")
    time.sleep(2)
s.close()
print("MySQL is ready!")
PY

uv run alembic upgrade head
exec uv run gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 1 \
  --threads 4 \
  --worker-class gthread \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  src.timerservice.wsgi:app
