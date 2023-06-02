#!/bin/bash

# Handles setting up the target user and redirecting the command to be executed
# by them.
# This is all in aid of ensuring that permissions of filesystem mapped volumes
# function correctly and that the root user is not used within the container.

eval "$(/opt/miniconda/bin/conda shell.bash hook)"
conda activate mantidimaging-dev

set -x
CMD=${1:-"bash"}
ARGS=${@:2}
runuser --command="${CMD} ${ARGS}"
