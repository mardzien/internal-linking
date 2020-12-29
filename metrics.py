import numpy as np
import time
from collections import namedtuple


Measurement = namedtuple('Measurement', ['start_time', 'end_time'])


class Metrics:
    # metrics = Metrics('processing_url')
    # metrics.start()
    # metrics.stop()
    # metrics.report()
    # metrics.reset()
    # metrics.durations()
    # metrics.total_duration()

    # statuses:
    # - idle
    # - pending

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.status = 'idle'
        self.measurements = list()
        self.start_time = None  # current measurement

    def start(self):
        self.status = 'pending'
        self.start_time = time.time()

    def stop(self):
        end_time = time.time()
        m = Measurement(self.start_time, end_time)
        self.start_time = None
        self.measurements.append(m)
        self.status = 'idle'

    def report(self):
        print(f"*************** {self.name} ****************")
        print("Total duration:", self.total_duration())
        print("Min:", self.min_duration())
        print("Max:", self.max_duration())
        print("Mean:", self.mean())
        print("Std dev:", self.std_dev())
        print("***********************************")

    def reset(self):
        self.measurements = list()
        self.start_time = None
        self.status = 'idle'

    def durations(self):
        return map(lambda x: x.end_time - x.start_time, self.measurements)

    def max_duration(self):
        arr = np.array(list(self.durations()))
        return arr.max()

    def min_duration(self):
        arr = np.array(list(self.durations()))
        return arr.min()

    def total_duration(self):
        arr = np.array(list(self.durations()))
        return arr.sum()

    def mean(self):
        arr = np.array(list(self.durations()))
        return arr.mean()

    def std_dev(self):
        arr = np.array(list(self.durations()))
        return arr.std()
