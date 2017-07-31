#!/usr/bin/env bash
imgpy_dir=$HOME/isis_imaging

# this will be used in the env script
python_exec="ipython"

# Call using . syntax, this will change this script's environment,
# i.e. all the variables defined within the -env script will be visible here
. $imgpy_dir/isis_imaging-env-py27.sh

PYTHONPATH="$imgpy_dir:$PYTHONPATH" ${python_location} -i $imgpy_dir/isis_imaging/ipython.py "$@"
