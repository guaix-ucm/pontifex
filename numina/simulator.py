

class Shutter(object):
    def __init__(self, cid=0):
        self.cid = cid
        self.opened = True

    def open(self):
        self.opened = True
        
    def close(self):
        self.opened = False

    
