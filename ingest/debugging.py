from multiprocessing import get_logger
import logging


def logger(level=logging.INFO):
    logger = get_logger()
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(levelname)s: %(asctime)s - %(process)s - %(message)s"))
    logger.addHandler(handler)

    return logger


app_logger = logger()
