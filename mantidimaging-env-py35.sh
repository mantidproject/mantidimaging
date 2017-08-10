#!/usr/bin/env bash

# set default to system python
python_location="/usr/bin/$python_exec"

anaconda_dir="$HOME/anaconda3"

# we expect a custom environment
py35_env="$anaconda_dir/envs/py35/bin"

# if anaconda is installed in default directory
if [ -d "$anaconda_dir" ]; then
    echo "Found anaconda at $py35_env"
    # update python executable to anaconda python
    python_location="${py35_env}/$python_exec"
    $python_location -V
fi
