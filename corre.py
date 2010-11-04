from datetime import datetime

from sqlalchemy import desc
import pyfits

from sql import ObsBlock, Images
from user import session

FORMAT = 'r%05d.fits'

def test_create_fits(filename):
    hdu = pyfits.PrimaryHDU()
    hdu.writeto('data/'+filename)

def exec_obsmode(instrument, obsmode, exposure, filter, repeat):

    # Add ObsBlock to database
    ob = ObsBlock(obsmode)
    ob.instrument = instrument
    ob.operator = 'Sergio'
    ob.start = datetime.utcnow()

    session.add(ob)
    session.commit()

    try:
        name, = session.query(Images.name).order_by(desc(Images.stamp)).first()
        number = int(name[1:-5]) + 1
    except TypeError:
        number = 0

    # Repeat
    for i in range(number, number + repeat):
        # create FITS
        try:
            filename = FORMAT % i
            test_create_fits(filename)
            img = Images(filename)
            img.exposure = exposure
            img.imgtype = obsmode
            img.stamp = datetime.utcnow()
            ob.images.append(img)
            session.commit()
        finally:
            pass

    # Finish ObsBlock in database
    ob.end = datetime.utcnow()
    session.commit()
