

__all__ = ['run']

def run(rb, pp, cp):
    return None

class Recipe:
    def __init__(self, pp, cp):
        pass

    @classmethod
    def requires(cls):
        return []

    def run(self, rb):
        return {'result': {'direct_image': 0, 'qa': 1}}

