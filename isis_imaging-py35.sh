#!/usr/bin/env bash
imgpy_dir=${HOME}/isis_imaging

# this will be used in the env script
python_exec="python"

. $imgpy_dir/isis_imaging-env-py35.sh

PYTHONPATH="$imgpy_dir:$PYTHONPATH" ${python_location} $imgpy_dir/isis_imaging/main.py "$@"
