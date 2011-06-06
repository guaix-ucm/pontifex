from threading import Thread, Event

# Periodic timer class
class PeriodicTimer(Thread):
    """
    Periodically call a function.

    PeriodicTimers are, like threads, started by calling their start()
    method. An attempt to ending them can be made by calling their
    end() method.

    PeriodicTimers use fixed-delay execution which means that the
    delay between subsequent invokations of the function is
    fixed. Because the execution time of the function is not accounted
    for, the periods therefore become more and more distorted in
    relation to real time. That makes PeriodicTimers unsuitable for
    long running threads in which it is critical that each function
    call time is as accurate as possible.

    For example:

        def hello():
            print "Hi there!"

        t = PeriodicTimer(5, hello)
        t.start()    # "Hi there!" will be printed every five seconds.
        
    """
    def __init__(self, interval, function, *args, **kwargs):
        """
        Create a PeriodicTimer that will repeatedly call function with
        arguments args and keyword arguments kwargs, after interval
        seconds have passed.
        """
        Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.finished = Event()

    def end(self):
        """
        Make a best effort attempt to stop the PeriodicTimer.

        If the thread is currently executing the function, this effort
        may not immidiately succeed. The PeriodicTimer is then stopped
        when execution returns from the function. If the function
        never returns, the thread will not be stopped.
        """
        self.finished.set()

    def run(self):
        while True:
            self.finished.wait(self.interval)
            if self.finished.isSet():
                break
            self.function(*self.args, **self.kwargs)

