#!/usr/bin/env bash
mantidimaging_dir=${HOME}/mantidimaging

# this will be used in the env script
python_exec="python"

# Call using . syntax, this will change this script's environment,
# i.e. all the variables defined within the -env script will be visible here
. $mantidimaging_dir/mantidimaging-env-py27.sh

PYTHONPATH="$mantidimaging_dir:$PYTHONPATH" ${python_location} $mantidimaging_dir/mantidimaging/main.py "$@"
