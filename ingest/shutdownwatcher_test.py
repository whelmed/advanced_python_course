import signal
import sched
import time
import os
import pytest
from ingest.shutdownwatcher import ShutdownWatcher
from unittest.mock import MagicMock


def teardown_function():
    """Remove handlers from all loggers"""
    import logging

    loggers = [logging.getLogger()] + \
        list(logging.Logger.manager.loggerDict.values())
    for logger in loggers:
        handlers = getattr(logger, "handlers", [])
        for handler in handlers:
            logger.removeHandler(handler)


@pytest.fixture(scope="function")
def watcher():
    return ShutdownWatcher()


@pytest.mark.parametrize("sig", [signal.SIGINT, signal.SIGTERM])
def test_shutdown_manager(watcher, sig):
    assert watcher.should_continue

    s = sched.scheduler(time.time, time.sleep)
    # Shedule the signal to be sent 0.2 seconds after s.run() is called.
    s.enter(0.1, 1, lambda: os.kill(os.getpid(), sig))

    with watcher as w:
        s.run()
        w.serve_forever()

    assert not watcher.should_continue
