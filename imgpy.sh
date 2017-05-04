# set default to system python
python_exec="/usr/bin/python"

anaconda_dir="$HOME/anaconda2"

if [ -d "$anaconda_dir" ]; then
	# update python executable to anaconda python
	python_exec="$anaconda_dir/bin/python"
fi

$python_exec $PWD/isis_imaging/main.py "$@"
