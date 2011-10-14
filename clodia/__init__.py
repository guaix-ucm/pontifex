
class Instrument(object):
    name = 'clodia'
    metadata = {'imagetype': 'IMGTYP',
                'airmass': 'AIRMASS',
                'exposure': 'EXPOSED',
                'juliandate': 'MJD-OBS',
                'detector.mode': 'CCDMODE',
                'filter0': 'FILTER'
                }
    detectors = [[256, 256]]
    amplifiers = [[[256, 256]]]
