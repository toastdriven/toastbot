#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name='toastbot',
    version='0.3.1',
    description='A clean, extensible IRC bot using irckit.',
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
)
