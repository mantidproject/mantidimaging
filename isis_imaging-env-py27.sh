#!/usr/bin/env bash

# set default to system python
python_location="/usr/bin/$python_exec"

anaconda_dir="$HOME/anaconda2"

# we expect a custom environment
py27="$anaconda_dir/bin"

# if anaconda is installed in default directory
if [ -d "$anaconda_dir" ]; then
    echo "Found anaconda at $py27"
    # update python executable to anaconda python
    python_location="${py27}/$python_exec"
fi
