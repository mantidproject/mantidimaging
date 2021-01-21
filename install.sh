# To run this script use source ./install.sh, or the version on master
# source <(curl -s https://raw.githubusercontent.com/mantidproject/mantidimaging/master/install.sh)
# source is used so that the shell environment is inherited - this is needed for conda access!
#
# Supported configuration:
# - ENVIRONMENT_NAME - specifies the environment name, default `mantidimaging`
#   - For nightly it will be called `mantidimaging_unstable`
# - REPO_LABEL - specifies the label from which it will be installed, default `main`,
#   - For nightly it will use `unstable`

if ! command -v conda &> /dev/null
then
    echo "'conda' not available, please activate Anaconda before calling this script"
    return
fi

env_name=${ENVIRONMENT_NAME:-mantidimaging}
repo_label=${REPO_LABEL:-main}

echo "Installing mantidimaging in environment with name '${env_name}' and repo label '${repo_label}'"

conda config --set always_yes yes

conda remove -n ${env_name} --all

conda config --prepend channels conda-forge  # for most of the deps
conda config --prepend channels astra-toolbox/label/dev # for astra
conda config --prepend channels dtasev  # for sarepy
conda config --prepend channels mantid # for mantidimaging

conda create -c mantid/label/${repo_label} -n ${env_name} mantidimaging python=3.8

conda activate ${env_name}
pip install pyqt5==5.15 pyqtgraph==0.11

conda config --set always_yes no
