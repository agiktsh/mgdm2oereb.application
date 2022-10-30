# -*- coding: utf-8 -*-

import os
import re
from glob import glob
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, 'README.md')) as f:
    README = f.read()
with open(os.path.join(HERE, 'CHANGES.md')) as f:
    CHANGES = f.read()
with open('requirements.txt') as f:
    re_ = a = re.compile(r'(.+)==')
    recommend = f.read().splitlines()
requires = [re_.match(r).group(1) for r in recommend]

with open('requirements-tests.txt') as f:
    re_ = a = re.compile(r'(.+)==')
    tests_require = f.read().splitlines()

setup(
    name='mgdm2oereb_service',
    version='0.0.1',
    description='A service based on pygeoapi to offer standard way of interacting with processing.',
    long_description='\n\n'.join([README, CHANGES]),
    long_description_content_type='text/markdown',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Framework :: pygeoapi",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: ASGI :: Application"
    ],
    author='Clemens Rudert',
    author_email='clemens@opengis.ch',
    project_urls={
        'Documentation': 'https://github.com/opengisch/mgdm2oereb.application/mgdm2oereb_service/blob/master/README.md',
        'Changelog': 'https://github.com/opengisch/mgdm2oereb.application/mgdm2oereb_service/blob/master/CHANGES.md',
        'Issue Tracker': 'https://github.com/mgdm2oereb.application/issues'
    },
    keywords=','.join([
        'mgdm2oereb',
        'INTERLIS',
        'ÖREB',
        'PLR'
    ]),
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'recommend': recommend,
        'no-version': requires,
        'testing': tests_require
    },
    entry_points={}
)
