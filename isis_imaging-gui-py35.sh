imgpy_dir=$HOME/isis_imaging


anaconda_dir="$HOME/anaconda3"
py35_env="$anaconda_dir/envs/py35/bin"

PYTHONPATH="$imgpy_dir:$PYTHONPATH" $py35_env/python $imgpy_dir/isis_imaging/main.py --gui "$@"
