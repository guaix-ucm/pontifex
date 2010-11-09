from Queue import Queue
from xmlrpclib import Server
import signal

class Instrument(object):
    def __init__(self, name, focus, obsmodes):
        self._name = name
        self._focus = focus
        self._obsmodes = obsmodes
        self.queue1 = Queue()
        self.seq = Server('http://localhost:8010')

    def name(self):
        return self._name

    def focus(self):
        return self._focus

    def obsmodes(self):
        return self._obsmodes

    def parser(self):
        pass

    def command(self, args):
        mandate = self.parser(args)
        self.queue1.put(mandate)

def siiill(obj):
    def handler(signum, frame):
	obj.unregister()
    signal.signal(signal.SIGHUP, handler)
