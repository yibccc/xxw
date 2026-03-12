"""Runtime service bootstrap for background workers."""
import threading
import time

from .scheduler.manager import start_scheduler
from .sse.hub import sse_hub

_runtime_started = False
_runtime_lock = threading.Lock()


def _start_ping_thread():
    """Start the background SSE keepalive publisher once."""
    def ping_loop():
        while True:
            time.sleep(30)
            sse_hub.publish_ping()

    thread = threading.Thread(target=ping_loop, daemon=True, name="sse-ping-thread")
    thread.start()
    return thread


def start_runtime_services():
    """Start background runtime services once per process."""
    global _runtime_started

    with _runtime_lock:
        if _runtime_started:
            return

        _start_ping_thread()
        start_scheduler()
        _runtime_started = True
