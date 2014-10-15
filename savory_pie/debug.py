import time

def report_time( name, start_time ):
    print( '{:<50}'.format("[" + name + "]") + ("%s ms" % ("{:>10}".format("{0:.2f}".format((time.time() - start_time) * 1000)))))

class TimeReporter:
    def __init__(self, name):
        self.name = name
        self.time_start = time.time()

    def report(self):
        report_time(self.name, self.time_start)
