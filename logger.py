import os
import sys
import datetime
import time
import functools

ADDON_DIR = os.path.dirname(__file__)
LOG_FILE = os.path.join(ADDON_DIR, "Anki_EDN_Stats.log")

def log(message, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message_file = f"[{timestamp}] [{level}] {message}\n"
    formatted_message_console = f"[EDN_Stats] [{timestamp}] [{level}] {message}"
    
    print(formatted_message_console, file=sys.stdout)
    sys.stdout.flush()
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted_message_file)
    except Exception as e:
        print(f"Error writing to log: {e}", file=sys.stderr)

def perf_log(func):
    """Decorator to measure and log function execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        log(f"PERFORMANCE: {func.__module__}.{func.__qualname__} pris {duration:.4f}s")
        return result
    return wrapper
