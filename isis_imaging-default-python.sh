#!/usr/bin/env bash
imgpy_dir=${HOME}/isis_imaging

# This will pick up whichever python is on the PATH
PYTHONPATH="$imgpy_dir:$PYTHONPATH" python $imgpy_dir/isis_imaging/main.py "$@"
