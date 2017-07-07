#!/usr/bin/env bash
imgpy_dir=$HOME/isis_imaging

# set default to system python
python_location="/usr/bin/${python_exec}"

anaconda_dir="$HOME/anaconda3"

# we expect a custom environment
py35_env="${anaconda_dir}/envs/py35/bin"

#anaconda_dir="$HOME/anaconda3"

# if anaconda is installed in default directory
if [ -d "$anaconda_dir" ]; then
	# update python executable to anaconda python
	python_location="${py35_env}/${python_exec}"
fi
