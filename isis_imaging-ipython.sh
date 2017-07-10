#!/usr/bin/env bash
imgpy_dir=$HOME/isis_imaging

# this will be used in the env script
python_exec="ipython"

. $imgpy_dir/isis_imaging-env.sh

PYTHONPATH="$imgpy_dir:$PYTHONPATH" ${python_location} -i $imgpy_dir/isis_imaging/ipython.py "$@"
