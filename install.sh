# To run this script use source ./install.sh, or the version on master
# source <(curl -s https://raw.githubusercontent.com/mantidproject/mantidimaging/master/install.sh)
# source is used so that the shell environment is inherited - this is needed for conda access!

if ! command -v conda &> /dev/null
then
    echo "'conda' not available, please activate Anaconda before calling this script"
    return
fi

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
