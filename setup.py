#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
import os

README = os.path.join(os.path.dirname(__file__), 'README.md')

setup(
    name='toastbot',
    version='0.4.1',
    description='A clean, extensible IRC bot using irckit.',
    long_description=open(README, 'r').read(),
    author='Daniel Lindsley',
    author_email='daniel@toastdriven.com',
    py_modules = ['toastbot'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ],
    url = 'http://github.com/toastdriven/toastbot'
)
