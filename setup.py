#!/usr/bin/env python

from distutils.core import setup

setup(name='pontifex',
      version='0.4.0',
      author='Sergio Pascual',
      author_email='sergiopr@fis.ucm.es',
      url='http://guaix.fis.ucm.es/~spr',
      license='GPLv3',
      description='Pontifex automatic reduction system',
      packages=['pontifex', 'pontifex.model', 'numina', 
                'emir', 'emir.recipes', 'megara', 'megara.recipes',
                'frida', 'frida.recipes', 'clodia', 'clodia.recipes'],
      scripts=['scripts/pontifex-server.py', 'scripts/pontifex-host.py'],
      classifiers=[
                   "Programming Language :: Python",
                   'Development Status :: 3 - Alpha',
                   "Environment :: Other Environment",
                   "Intended Audience :: Science/Research",
                   "License :: OSI Approved :: GNU General Public License (GPL)",
                   "Operating System :: OS Independent",
                   "Topic :: Scientific/Engineering :: Astronomy",
                   ],
)
