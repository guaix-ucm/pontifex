
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
    	_logger.info('starting direct imaging reduction')
        _logger.info('basic processing')
        _logger.info('resizing images and masks')
        _logger.info('superflat correction')
        _logger.info('simple sky correction')
        _logger.info('stacking science images')
    	time.sleep(5)
    	_logger.info('direct imaging reduction ended')
        return 0
