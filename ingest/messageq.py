import contextlib
import os
from collections import namedtuple
from multiprocessing import Event, Queue, Value
from multiprocessing.managers import BaseManager
from queue import Empty
from typing import Any, List

from .debugging import app_logger as log


class QueueWrapper(object):

    def __init__(self, name: str, q: Queue = None, prevent_writes: Event = None):
        self.name: str = name
        self.q: Queue = q or Queue()
        self._prevent_writes: Event = prevent_writes or Event()

    def connect(self):
        '''Connect to multiprocessing.Queue
        Used by clients attempting to connect to the Queue via a proxy.
        '''
        self.q.connect()

    def get(self) -> Any:
        '''This call blocks until a it gets a message from the queue.
        If the queue is drained, it returns the sentinal string STOP.
        If the queue is closed while this call is blocking, it'll return STOP
        '''
        if self.is_drained:
            return 'STOP'
        try:
            return self.q.get()
        except Exception as ex:
            log.info(f'q.get() interupted')
            return 'STOP'

    def put(self, obj: object):
        if self.is_writable:
            log.debug('putting message on the queue')
            self.q.put(obj)

    def put_many(self, objs: List[object]):
        for obj in objs:
            self.put(obj)

    def prevent_writes(self):
        '''Prevent external writes to the queue. 
        This is useful for shutting down, or dealing with back pressure.
        '''
        log.debug(f'preventing writes to the {self.name} queue')
        self._prevent_writes.set()

    @ property
    def is_writable(self):
        '''Read-only property indicating if the queue is writable. '''
        return not self._prevent_writes.is_set()

    @ property
    def is_drained(self):
        '''If the queue is not writable and is empty the queue is draining '''
        return not self.is_writable and self.empty

    @ property
    def empty(self):
        '''Read-only property indicating if the queue is empty '''
        return self.q.empty()

    def close(self):
        self.q.close()


class QueueManager(BaseManager):
    pass


def register_manager(name: str, queue: QueueWrapper = None):
    if queue:
        QueueManager.register(name, callable=lambda: queue)
    else:
        QueueManager.register(name)


def create_queue_manager(port: int) -> QueueManager:
    '''Binds to 127.0.0.1 on the given port. 
    Using localhost on at least Debian systems results in extremly slow put() calls.
    '''
    return QueueManager(address=('127.0.0.1', port), authkey=b'ingestbackend')
