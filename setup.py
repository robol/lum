#!/usr/bin/env python

from distutils.core import setup

setup(name='Lum',
      version='0.1',
      description='Ldap User Manager',
      author='Leonardo Robol',
      author_email='robol@poisson.phc.unipi.it',
      url='http://poisson.phc.unipi.it/~robol/wordpress/programmi/lum/',
      packages=['lum', 'lum.interface'],
      scripts = ['lum.py'],
      package_data = {'lum.interface': ['ui/*.ui', 'ui/*.png']},
     )
