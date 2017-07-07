#!/usr/bin/env bash
imgpy_dir=${HOME}/isis_imaging

# this will be used in the env script
python_exec="python"

. isis_imaging-env.sh

PYTHONPATH="$imgpy_dir:$PYTHONPATH" ${python_location} $imgpy_dir/isis_imaging/main.py --gui "$@"
