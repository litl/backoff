# coding:utf-8

import backoff

from distutils import core


classifiers = ['Development Status :: 5 - Production/Stable',
               'Intended Audience :: Developers',
               'Programming Language :: Python',
               'License :: OSI Approved :: MIT License',
               'Natural Language :: English',
               'Operating System :: OS Independent',
               'Programming Language :: Python',
               'Programming Language :: Python :: 2.6',
               'Programming Language :: Python :: 2.7',
               'Programming Language :: Python :: 3',
               'Programming Language :: Python :: Implementation',
               'Programming Language :: Python :: Implementation :: CPython',
               'Topic :: Internet :: WWW/HTTP',
               'Topic :: Software Development :: Libraries :: Python Modules',
               'Topic :: Utilities']

version = backoff.__version__
url = "https://github.com/litl/backoff"
tarball_url = "%s/tarball/v%s" % (url, version)


def readme():
    with open("README.rst", "r") as infile:
        return infile.read()


core.setup(name='backoff',
           version=version,
           description="Function decoration for backoff and retry",
           long_description=readme(),
           packages=['backoff'],
           author="Bob Green",
           author_email="rgreen@goscoutgo.com",
           keywords = "backoff function decorator",
           url=url,
           download_url=tarball_url,
           license="MIT",
           classifiers=classifiers)
