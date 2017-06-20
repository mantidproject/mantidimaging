imgpy_dir=$HOME/isis_imaging

# set default to system python
python_exec="/usr/bin/ipython"

anaconda_dir="$HOME/anaconda2"

# if anaconda is installed in default directory
if [ -d "$anaconda_dir" ]; then
	# update python executable to anaconda python
	python_exec="$anaconda_dir/bin/ipython"
fi

PYTHONPATH="$imgpy_dir:$PYTHONPATH" $python_exec -i $imgpy_dir/isis_imaging/ipython.py "$@"
