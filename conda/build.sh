echo ===== BUILD.SH STARTED =====
python conda/make_versions.py
python -m pip install --ignore-installed .
rm mantidimaging/versions.py
