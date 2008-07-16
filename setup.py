#!/usr/bin/env python

from distutils.core import setup
from version import VERSION

setup(name="omnisync",
      version=VERSION,
      description="Multiprotocol file synchroniser.",
      author="Stavros Korokithakis",
      author_email="stavros@korokithakis.net",
      url="http://launchpad.net/omnisync/",
      packages=["omnisync"],
      requires=["paramiko", "boto"],
      scripts=["omnisync"]
     )
