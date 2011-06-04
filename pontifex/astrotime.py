import datetime

# MJD 0 is 1858-11-17 00:00:00.00 
_MJDREF = datetime.datetime(year=1858, month=11, day=17)

def datetime_to_mjd(dt):
    diff = dt - _MJDREF
    result  = diff.days + (diff.seconds + diff.microseconds / 1e6) / 86400.0
    return result

