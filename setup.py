#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
    
from omnisync.version import VERSION

setup(name="omnisync",
    version=VERSION,
    description="Multiprotocol file synchroniser.",
    author="Stavros Korokithakis",
    author_email="stavros@korokithakis.net",
    license="Simplified BSD License",
    url="http://launchpad.net/omnisync/",
    packages=["omnisync", "omnisync.transports"],
    requires=["paramiko", "boto"],
    entry_points = { 
    'console_scripts':[
        'omnisync = omnisync.main:main'
    ]},  
)
