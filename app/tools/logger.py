import logging

_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
logging.basicConfig(level=logging.INFO, format=_FORMAT)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
