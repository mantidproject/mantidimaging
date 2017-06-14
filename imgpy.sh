imgpy_dir=$HOME/imgpy

# set default to system python
python_exec="/usr/bin/python"

anaconda_dir="$HOME/anaconda2"

# if anaconda is installed in default directory
if [ -d "$anaconda_dir" ]; then
	# update python executable to anaconda python
	python_exec="$anaconda_dir/bin/python"
fi

PYTHONPATH="$imgpy_dir:$PYTHONPATH" $python_exec $imgpy_dir/isis_imaging/main.py "$@"
