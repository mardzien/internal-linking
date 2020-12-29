import time
from collections import namedtuple

# metrics = Metrics('processing_url')
# metrics.start()
# metrics.stop()
# metrics.report()
# metrics.reset()


Measurement = namedtuple('Measurement', ['start_time', 'end_time'])


# statuses:
# - idle
# - pending

class Metrics:
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
        raise NotImplementedError()

    def reset(self):
        self.measurements = list()
        self.start_time = None
        self.status = 'idle'
