echo on
echo "Start bld.bat"
python conda\make_versions.py
python -m pip install --ignore-installed .
del mantidimaging\versions.py
echo "Finished bld.bat"
