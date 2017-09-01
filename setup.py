#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import sys
from shutil import rmtree

from setuptools import Command, find_packages, setup

NAME = 'dlen'
DESCRIPTION = 'Dlen checks the length of the functions. '
URL = 'https://github.com/Endika/dlen'
EMAIL = 'me@endikaiglesias.com'
AUTHOR = 'Endika Iglesias'
KEYWORDS = 'Refactor, Python, Python2, Python3, Refactoring, def, class, Clean'

REQUIRED = []

here = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

about = {}
with open(os.path.join(here, NAME, '__version__.py')) as f:
    exec(f.read(), about)


class PublishCommand(Command):
    """Support setup.py publish."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Print things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        """Initialize options."""
        pass

    def finalize_options(self):
        """Finalize options."""
        pass

    def run(self):
        """Run."""
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except Exception:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(
            sys.executable))

        self.status('Uploading the package to PyPi via Twine…')
        os.system('twine upload dist/*')

        sys.exit()


setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    packages=find_packages(exclude=('tests',)),
    py_modules=['dlen'],
    entry_points={
        'console_scripts': ['dlen=dlen:main'],
    },
    install_requires=REQUIRED,
    include_package_data=True,
    license='MIT',
    keywords=KEYWORDS,
    classifiers=[
        'Development Status :: 6 - Mature',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Environment :: Console',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities'
    ],
    cmdclass={
        'publish': PublishCommand,
    },
)
