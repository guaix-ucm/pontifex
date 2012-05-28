#!/usr/bin/env python

from distutils.core import setup

setup(name='pontifex',
      version='0.4.2',
      author='Universidad Complutense de Madrid',
      author_email='sergiopr@fis.ucm.es',
      url='http://guaix.fis.ucm.es/~spr',
      license='GPLv3',
      description='Pontifex automatic reduction system',
      packages=['pontifex', 'pontifex.model', 'pontifex.user'],
      package_dir={'pontifex': 'src/pontifex'},
      scripts=['scripts/pontifex-server.py', 'scripts/pontifex-host.py'],
      install_requires=['numina', 'sqlalchemy'],
      classifiers=[
                   "Programming Language :: Python :: 2.7",
                   'Development Status :: 3 - Alpha',
                   "Environment :: Other Environment",
                   "Intended Audience :: Science/Research",
                   "License :: OSI Approved :: GNU General Public License (GPL)",
                   "Operating System :: OS Independent",
                   "Topic :: Scientific/Engineering :: Astronomy",
                   ],
)
