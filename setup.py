#!/usr/bin/env python

import os
from setuptools import setup, find_packages
from sphinx.setup_command import BuildDoc

THIS_PATH = os.path.dirname(__file__)


setup(
    name='mantidimaging',
    version='0.9',
    packages=find_packages(),
    py_modules=['mantidimaging'],
    entry_points={
        'console_scripts': [
            'mantidimaging = mantidimaging.main:cli_main',
            'mantidimaging-ipython = mantidimaging.ipython:main'
        ],
        'gui_scripts': [
            'mantidimaging-gui = mantidimaging.main:gui_main'
        ]
    },
    url='https://github.com/mantidproject/mantidimaging',
    license='GPL-3.0',
    author='Dimitar Tasev',
    author_email='dimitar.tasev@stfc.ac.uk',
    description='MantidImaging Tomographic Reconstruction package',
    long_description=open("README.md").read(),
    platforms=["Linux"],
    test_suite='nose.collector',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Natural Language :: English',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'Operating System :: POSIX :: Linux',
        'Topic :: Scientific/Engineering',
        'Topic :: Imaging',
        'Topic :: Tomographic Reconstruction',
    ],
    cmdclass={
        'docs': BuildDoc
    },
    extras_require={
        'testing': [
            'nose',
            'nose-randomly'
        ],
    },
    tests_require=[
        'nose',
        'nose-randomly'
    ],
    install_requires=[
        'numpy'
    ]
)
