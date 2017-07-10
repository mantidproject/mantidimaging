#!/usr/bin/env bash

# set default to system python
python_location="/usr/bin/$python_exec"

anaconda_dir="$HOME/anaconda3"

# we expect a custom environment
#py35_env="$anaconda_dir/envs/py35/bin"
py27="$HOME/anaconda2/bin"

# if anaconda is installed in default directory
if [ -d "$anaconda_dir" ]; then
	# update python executable to anaconda python
	python_location="${py27}/$python_exec"
fi
