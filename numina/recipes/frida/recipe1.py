
import logging
import time

__all__ = ['run']

_logger = logging.getLogger('numina.recipes.frida')

def run(rb, pp, cp):
    return None

class Recipe:
    def __init__(self, pp, cp):
        pass

    @classmethod
    def requires(cls):
        return []

    def run(self, rb):
    	_logger.info('starting bias reduction')
    	time.sleep(5)
    	_logger.info('bias reduction ended')
        return 0
