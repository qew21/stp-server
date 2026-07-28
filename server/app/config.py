from dynaconf import Dynaconf


account = Dynaconf(envvar_prefix="STP", load_dotenv=True, environments=True, settings_files=["account.yaml"])


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s - %(levelname)s - %(name)s:%(lineno)s - %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(asctime)s - %(levelname)s - %(name)s:%(lineno)s - %(client_addr)s - "%(request_line)s" %(status_code)s',
        },
    },
    "handlers": {
        "console": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "default": {
            "formatter": "default",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "./log/app.log",
            "when": "midnight",
        },
        "access": {
            "formatter": "access",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "./log/access.log",
            "when": "midnight",
        },
        "subscribe": {
            "formatter": "default",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "./log/subscribe.log",
            "when": "midnight",
        },
    },
    "loggers": {
        "": {"handlers": ["default", "console"], "level": "DEBUG", "propagate": False},
        "subscribe": {"handlers": ["subscribe", "console"], "level": "DEBUG", "propagate": False},
        "uvicorn.error": {"handlers": ["default", "console"], "level": "DEBUG", "propagate": False},
        "uvicorn.access": {"handlers": ["access"], "level": "DEBUG", "propagate": False},
    },
}


