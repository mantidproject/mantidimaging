#!/usr/bin/env bash
imgpy_dir=${HOME}/isis_imaging

# this will be used in the env script
python_exec="python"

# Call using . syntax, this will change this script's environment,
# i.e. all the variables defined within the -env script will be visible here
. $imgpy_dir/isis_imaging-env-py27.sh

PYTHONPATH="$imgpy_dir:$PYTHONPATH" $python_location $imgpy_dir/isis_imaging/main.py --gui -i . "$@"
