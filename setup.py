# coding:utf-8

import backoff

from distutils import core


classifiers = ['Development Status :: 5 - Production/Stable',
               'Intended Audience :: Developers',
               'Programming Language :: Python',
               'License :: OSI Approved :: MIT License',
               'Natural Language :: English',
               'Operating System :: OS Independent',
               'Operating System :: MacOS',
               'Operating System :: POSIX',
               'Operating System :: POSIX :: Linux',
               'Programming Language :: Python',
               'Programming Language :: Python :: 2.6',
               'Programming Language :: Python :: 2.7',
               'Programming Language :: Python :: 3',
               'Programming Language :: Python :: Implementation',
               'Programming Language :: Python :: Implementation :: CPython',
               'Topic :: Internet :: WWW/HTTP',
               'Topic :: Software Development :: Libraries :: Python Modules',
               'Topic :: Utilities']


core.setup(name='backoff',
           version='1.0.6',
           py_modules=['backoff'],
           author="Bob Green",
           author_email="bgreen@litl.com",
           description="Function decoration for backoff and retry",
           keywords = "backoff function decorator",
           url="https://github.com/litl/backoff",
           download_url="https://github.com/litl/backoff/tarball/v1.0.6",
           license="MIT",
           long_description=backoff.__doc__,
           classifiers=classifiers)
