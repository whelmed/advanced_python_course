import signal
import time
from typing import Callable, List
from .debugging import app_logger as log


class ShutdownWatcher:
    """ ShutdownWatcher listens for the signals: SIGINT, SIGTERM.
        When the app is signaled to shutdown it sets should_continue to False.

        Example usage:

        with ShutdownWatcher() as watcher:
            watcher.serve_forever() # <-- Blocks until signaled.
    """

    def __init__(self):
        self.should_continue = True

        for s in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(s, self.exit)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.exit()

    def serve_forever(self):
        while self.should_continue:
            time.sleep(0.1)

    def exit(self, *args, **kwargs):
        self.should_continue = False
