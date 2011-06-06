from SocketServer import ThreadingMixIn
from SimpleXMLRPCServer import SimpleXMLRPCServer

class txrServer(ThreadingMixIn, SimpleXMLRPCServer):
      pass
