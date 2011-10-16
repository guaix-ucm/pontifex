#
# Copyright 2011 Sergio Pascual
# 
# This file is part of Pontifex
# 
# Pontifex is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Pontifex is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Pontifex.  If not, see <http://www.gnu.org/licenses/>.
#

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

