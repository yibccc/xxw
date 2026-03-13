"""Gunicorn WSGI entrypoint."""

from .app import create_app
from .runtime import start_runtime_services

app = create_app()
start_runtime_services()
