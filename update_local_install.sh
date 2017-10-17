#!/bin/sh

# Helper script to automatically update an installation from Git checkout to
# the latest version.

git pull origin master
python setup.py develop
