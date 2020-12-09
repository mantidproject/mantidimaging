.. _Troubleshooting:

Troubleshooting
===============

Can't reconstruct with FBP_CUDA and SIRT_CUDA
---------------------------------------------

These algorithms have 2 requirements:

- Having a CUDA-compatible graphics card (GPU)
- Having the CUDA Runtime 10.2 libraries installed


Having a CUDA-compatible graphics card
######################################

Please check that your GPU is on the list of compatible GPUs https://developer.nvidia.com/cuda-gpus

Having the CUDA Runtime 10.2 libraries installed
################################################

Please install the CUDA Runtime version 10.2 binaries from https://developer.nvidia.com/cuda-10.2-download-archive

Reinstalling CUDA on Linux can be quickly done with this script


.. code-block:: bash

    # uninstall nvidia driver and cuda driver
    nvidia-uninstall && /usr/local/cuda/bin/cuda-uninstaller

    # download the CUDA installer
    wget http://developer.download.nvidia.com/compute/cuda/10.2/Prod/local_installers/cuda_10.2.89_440.33.01_linux.run ~/Downloads/cuda_10.2.89_440.33.01_linux.run

    # install GPU driver and CUDA Toolkit from CLI silently
    sudo bash ~/Downloads/cuda_10.2.89_440.33.01_linux.run --silent --driver --toolkit
