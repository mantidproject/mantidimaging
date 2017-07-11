#!/usr/bin/env python

from setuptools import setup, find_packages
import os

THIS_PATH = os.path.dirname(__file__)
setup(
    name='isis_imaging',
    version='0.9',
    packages=find_packages(),
    py_modules=['isis_imaging'],
    url='https://github.com/mantidproject/isis_imaging',
    license='GPL-3.0',
    author='Dimitar Tasev',
    author_email='dimitar.tasev@stfc.ac.uk',
    tests_require=['nose'],
    description='ISIS Imaging Tomographic Reconstruction package',
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
    extras_require={
        'testing': ['nose'],
    },
    long_description=open("README.md").read(), install_requires=['numpy'])
