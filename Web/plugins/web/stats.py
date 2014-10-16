__author__ = 'Gareth Coles'

import psutil
import time

from collections import deque
from twisted.internet import task

from system.singleton import Singleton


class Stats(object):
    """
    Statistics about this process and the machine itself.

    This uses fixed-length queues to store up to 20 items of each statistic.
    """

    __metaclass__ = Singleton

    cpu = deque(maxlen=20)
    ram = deque(maxlen=20)

    process = psutil.Process()

    looping_callback = None

    def _get_timestamp(self):
        return int(round(time.time() * 1000))

    def __init__(self):
        pass

    def start(self):
        self.cpu.clear()
        self.ram.clear()

        self.looping_callback = task.LoopingCall(self.task)
        self.looping_callback.start(5.0)

    def stop(self):
        self.looping_callback.stop()

    def get_cpu(self):
        return list(self.cpu)

    def get_ram(self):
        return list(self.ram)

    def get_cpu_latest(self):
        return self.cpu[-1]

    def get_ram_latest(self):
        return self.ram[-1]

    def get_ram_total(self):
        return (float(psutil.virtual_memory().total) / 1024) / 1024

    def task(self):
        self.cpu.append([
            self.process.cpu_percent(),
            self._get_timestamp()
        ])
        self.ram.append([
            (float(self.process.memory_info().rss) / 1024) / 1024,
            self._get_timestamp()
        ])
