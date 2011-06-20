
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4port os

'''Parse instrument files'''

import ConfigParser
import logging

_logger = logging.getLogger('parser')

class InstrumentDescription(object):
    pass

class WheelDescription(object):
    pass

class AmplifierDescription(object):
    pass

class SpectrographDescription(object):
    pass

class GrismDescription(object):
    pass

class DetectorDescription(object):
    pass

def parse_instrument(fd):
    config = ConfigParser.SafeConfigParser()
    config.read(fd)

    ins = InstrumentDescription()
    ins.spectrographs = []

    # read instrument
    _logger.debug('reading %s', 'instrument')
    ins.name = config.get('instrument', 'name')
    ins.version = config.get('instrument', 'version')
    nspec = config.getint('instrument', 'spectrographs')

    for sidx in range(nspec):
        sp = SpectrographDescription()
        _logger.debug('reading spectrograph_%i', sidx)

        nwheel = config.getint('spectrograph_%i' % sidx, 'wheels')
        sp.wheels = []
        dfunc = lambda x: 'wheel_%d' % x
  
        wheel = WheelDescription()
        dlabel = dfunc(sidx)
        _logger.debug('reading %s', dlabel)
        namp = config.getint(dlabel, 'elements')

        afunc = lambda x: 'grism_%d_%d' % (sidx, x)
        wheel.grisms = []
        sp.wheels.append(wheel)

        for j in range(namp):
            amp = GrismDescription()
            alabel = afunc(j)
            amp.name = config.get(alabel, 'name')
            wheel.grisms.append(amp)
            _logger.debug('reading %s', alabel)

        ndetect = config.getint('spectrograph_%i' % sidx, 'detectors')
        dfunc = lambda x: 'detector_%d' % x

        sp.detectors = []

        for i in range(ndetect):
            det = DetectorDescription()
            dlabel = dfunc(sidx)
            _logger.debug('reading %s', dlabel)
            namp = config.getint(dlabel, 'amplifiers')

            det.model = config.get(dlabel, 'model')
            det.shape = eval(config.get(dlabel, 'shape'))
            det.bias = config.getfloat(dlabel, 'bias')
            det.dark = config.getfloat(dlabel, 'dark')
            det.gain = config.getfloat(dlabel, 'gain')
            det.ron = config.getfloat(dlabel, 'ron')

            afunc = lambda x: 'amp_%d_%d' % (sidx, x)
            amps = []
            det.amps = amps
            sp.detectors.append(det)

            for j in range(namp):
                amp = AmplifierDescription()
                alabel = afunc(j)
                amp.gain = config.getfloat(alabel, 'gain')
                amp.ron = config.getfloat(alabel, 'ron')
                shape = eval(config.get(alabel, 'shape'))
                amp.shape = tuple(slice(*p) for p in shape)
                amps.append(amp)
                _logger.debug('reading %s', alabel)

        ins.spectrographs.append(sp)

    return ins

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
