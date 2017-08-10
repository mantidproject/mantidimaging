#!/usr/bin/env bash
mantidimaging_dir=${HOME}/mantidimaging

# This doesn't call any environment scripts and will just call the system python

# This will pick up whichever python is on the PATH
PYTHONPATH="$mantidimaging_dir:$PYTHONPATH" python $mantidimaging_dir/mantidimaging/main.py --gui -i . "$@"
