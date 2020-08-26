conda config --set always_yes yes

conda remove -n mantidimaging --all

conda config --prepend channels conda-forge  # for most of the deps
conda config --prepend channels astra-toolbox/label/dev # for astra
conda config --prepend channels dtasev  # for sarepy
conda config --prepend channels mantid  # for mantidimaging

conda create -n mantidimaging mantidimaging

conda activate mantidimaging
pip install pyqt5==5.15

conda config --set always_yes no
