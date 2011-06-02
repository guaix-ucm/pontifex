
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4port os

'''Parse instrument files'''

import ConfigParser
import logging

_logger = logging.getLogger('parser')

class InstrumentDescription(object):
    pass

class AmplifierDescription(object):
    pass

class DetectorDescription(object):
    pass

def parse_instrument(fd):
    config = ConfigParser.SafeConfigParser()
    config.read(fd)

    ins = InstrumentDescription()

    # read instrument
    _logger.debug('reading %s', 'instrument')
    ins.name = config.get('instrument', 'name')
    ins.version = config.get('instrument', 'version')
    # read image
    _logger.debug('reading %s', 'image')
    ndetect = config.getint('image', 'detectors')
    
    dfunc = lambda x: 'detector_%d' % x

    ins.dets = []

    for i in range(ndetect):
        det = DetectorDescription()
        dlabel = dfunc(i)
        _logger.debug('reading %s', dlabel)
        namp = config.getint(dlabel, 'amplifiers')

        det.model = config.get(dlabel, 'model')
        det.shape = eval(config.get(dlabel, 'shape'))
        det.bias = config.getfloat(dlabel, 'bias')
        det.dark = config.getfloat(dlabel, 'dark')
        det.gain = config.getfloat(dlabel, 'gain')
        det.ron = config.getfloat(dlabel, 'ron')

        afunc = lambda x: 'amp_%d_%d' % (i, x)
        amps = []
        det.amps = amps
        ins.dets.append(det)

        for j in range(namp):
            amp = AmplifierDescription()
            alabel = afunc(j)
            amp.gain = config.getfloat(alabel, 'gain')
            amp.ron = config.getfloat(alabel, 'ron')
            shape = eval(config.get(alabel, 'shape'))
            amp.shape = tuple(slice(*p) for p in shape)
            amps.append(amp)
            _logger.debug('reading %s', alabel)

    ins.detectors = ins.dets
    del ins.dets

    return ins

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
