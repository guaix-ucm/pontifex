
class Image(object):
    def __init__(self):
        self.id = None
        self.path = None

class ReductionBlock(object):
    def __init__(self):
        self.id = None
        self.instrument = None
        self.mode = None
        self.other = None
        self.images = []

class ReductionResult(object):
    def __init__(self):
        self.id = None
        self.reduction_block = None
        self.other = None
        self.status = 0
        self.picklable = {}

