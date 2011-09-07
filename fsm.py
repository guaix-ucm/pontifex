#!/usr/bin/python

import logging.config

logging.config.fileConfig('logging.ini')

from numina import main
from numina import model

if __name__ == '__main__':

    rb = model.ReductionBlock()

    rb.id = 1
    rb.instrument = 'emir'
    rb.mode = 'mode1'
    
    for i in range(12):
        im = model.Image()
        im.id = i + 1    
        im.path = 'r%05d.fits' % i
        rb.images.append(im)

    main(rb)
