"""
Logging is essential for understanding application behavior, debugging issues, and monitoring performance. 

1- logging levels:

    - DEBUG: For detailed diagnostic information
    - INFO: For tracking normal application flow
    - WARNING: For potentially harmful situations
    - ERROR: For errors that might still allow the application to continue running
    - CRITICAL: For severe errors that will prevent the application from continuing

    DEBUG ───┬──→ DEBUG messages show
    INFO  ───┼──→ INFO messages show  
    WARNING ─┼──→ WARNING messages show
    ERROR  ──┼──→ ERROR messages show
    CRITICAL ─┴──→ CRITICAL messages show

    If you set level=INFO, you'll see:
    INFO, WARNING, ERROR, and CRITICAL messages
    (but NOT DEBUG messages)

2. Formatters - How Log Messages Look

    %(asctime)s - Timestamp

    %(name)s - Logger name (usually module name)

    %(levelname)s - Log level (DEBUG, INFO, etc.)

    %(message)s - The actual log message

    %(filename)s - Python filename

    %(lineno)d - Line number in the file

3. Handlers - Where Logs Go

Three different output destinations:

    console handler:

        Level: INFO and above

        Output: Standard output (terminal)

        Format: Standard format

        Shows: INFO, WARNING, ERROR, CRITICAL

    file handler:

        Level: DEBUG and above (everything)

        Output: app.log file

        Format: Detailed format (with filename/line number)

        Mode: 'a' (append - adds to existing file)

        Shows: DEBUG, INFO, WARNING, ERROR, CRITICAL

    error_file handler:

        Level: WARNING and above (only errors)

        Output: errors.log file

        Format: Detailed format

        Mode: 'a' (append)

        Shows: WARNING, ERROR, CRITICAL

3.1 Mode: 'a' and other options

    When you define a file handler in Python logging, you can set the file mode:

    'a' (append) → Default.
        New logs are added to the end of the existing file. Old logs are kept.
        Useful when you want a continuous log history.

    'w' (write / overwrite)
        Every time you restart the app, the log file is cleared and new logs overwrite it.
        Useful if you only want the most recent logs (no history).

    'x' (exclusive creation)
        Creates a new file, but if the file already exists, it raises an error.
        Rarely used for logs, but ensures you never overwrite old logs accidentally.
"""

import logging
import logging.config
import os
from app_config import app_settings
# ---------- Formatters ----------
FORMATTERS = {
    "simple": {
        "format": "[%(levelname)s] %(message)s"
    },
    "detailed": {
        "format": "%(asctime)s %(name)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s"
    },
    "json": {
        "format": '{"time": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
    },
}

# ---------- Handlers ----------
HANDLERS = {
    "console": {
        "class": "logging.StreamHandler",
        "level": "DEBUG",
        "formatter": "simple",
        "stream": "ext://sys.stdout",
    },
    "file": {
        "class": "logging.FileHandler",
        "level": "DEBUG",
        "formatter": "detailed",
        "filename": "logs/app.log",
        "mode": "a",
    },
    "error_file": {
        "class": "logging.FileHandler",
        "level": "ERROR",
        "formatter": "detailed",
        "filename": "logs/errors.log",
        "mode": "w",
    },
}

# ---------- Development ----------

development = {
        # Version and Basic Settings
        'version': 1, # Specifies the schema version (always 1 for this format)
        'disable_existing_loggers': False, # False don’t break other libraries’ logging, keep their loggers alive
        # disable_existing_loggers: True = “wipe the slate clean, silence any loggers you haven’t redefined.”
        "formatters": FORMATTERS,
        "handlers": HANDLERS,
        "loggers": {
            "": {  # Root
                "handlers": ["console", "file", "error_file"],
                "level": "DEBUG",
                "propagate": True,
            },
            "my_app": {
                "handlers": ["console", "file", "error_file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "third_party": {
                "handlers": ["file"],
                "level": "WARNING",
                "propagate": False,
            },
        },
    }

# ---------- Testing ----------
testing = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": FORMATTERS,
        "handlers": {
            "console": HANDLERS["console"]
        },
        "loggers": {
            "": {  # Root only console
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": False,
            }
        },
    }


# ---------- Production ----------
production = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": FORMATTERS,
        "handlers": {
            "console": {
                **HANDLERS["console"],
                "level": "WARNING",  # Less noisy in production
            },
            "file": HANDLERS["file"],
            "error_file": HANDLERS["error_file"],
        },
        "loggers": {
            "": {  # Root
                "handlers": ["console", "file", "error_file"],
                "level": "INFO",  # Only INFO+ in production
                "propagate": True,
            },
            "my_app": {
                "handlers": ["file"],
                "level": "INFO",
                "propagate": False,
            },
            "third_party": {
                "handlers": ["file"],
                "level": "ERROR",
                "propagate": False,
            },
        },
    }




# ---------- Environments ----------
CONFIGS = {
    "development": development,

    "testing": testing,

    "production": production,
}



# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)
# ---------- Apply Config ----------

print(f"Applying logging config...{app_settings.APP_ENV}")
logging.config.dictConfig(CONFIGS[app_settings.APP_ENV])
