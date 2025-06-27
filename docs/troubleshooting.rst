.. _Troubleshooting:

Troubleshooting
===============

Can't reconstruct with FBP_CUDA and SIRT_CUDA
---------------------------------------------

These algorithms have 2 requirements:

- Having a CUDA-compatible graphics card (GPU)
- Having the CUDA Runtime 10.2 libraries installed


Having a CUDA-compatible graphics card
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Please check that your GPU is on the list of compatible GPUs: https://developer.nvidia.com/cuda-gpus

Having the CUDA Runtime 10.2 libraries installed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Please install the CUDA Runtime version 10.2 binaries from https://developer.nvidia.com/cuda-10.2-download-archive

Reinstalling CUDA on Linux can be quickly done with this script:


.. code-block:: bash

    # uninstall nvidia driver and cuda driver
    nvidia-uninstall && /usr/local/cuda/bin/cuda-uninstaller

    # download the CUDA installer
    wget http://developer.download.nvidia.com/compute/cuda/10.2/Prod/local_installers/cuda_10.2.89_440.33.01_linux.run ~/Downloads/cuda_10.2.89_440.33.01_linux.run

    # install GPU driver and CUDA Toolkit from CLI silently
    sudo bash ~/Downloads/cuda_10.2.89_440.33.01_linux.run --silent --driver --toolkit


Specific Errors
===============


SystemError: <built-in function connectSlotsByName> returned a result with an error set
---------------------------------------------------------------------------------------

This means that the PyQt package is missing or an old version (it must be newer than PyQt5==5.13.2).

Suggested Fix
^^^^^^^^^^^^^

Install PyQt5 and pyqtgraph with :code:`pip install pyqt5==5.15 pyqtgraph==0.12`.



qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found
-----------------------------------------------------------------------------------------

This might mean that some system libraries are missing.

Suggested Fix
^^^^^^^^^^^^^

Try installing :code:`apt install libxcb-xinerama0`.



qt.qpa.xcb: could not connect to display...
-------------------------------------------

Missing :code:`DISPLAY` variable. This means the application cannot find the display to show itself on.

Suggested Fix
^^^^^^^^^^^^^

You can set this via :code:`export DISPLAY=:N` where :code:`:N` should be the number of your display.



IDAaaS Terminal Error Messages
------------------------------
Errors from the terminal when Mantid Imaging is launched, such as:

:code:`ERROR: ld.so: object 'libdlfaker.so' from LD_PRELOAD cannot be preloaded: ignored.`

These are harmless and can be ignored.

UserWarning: CUDA path could not be detected. Set CUDA_PATH environment variable if CuPy failed to load
----------------------------------------------------------------------------------------------------------
This warning likely indicates that the  :code:`CUDA_PATH` environment variable is not set correctly, or that the CUDA Toolkit is not installed on your system.

If Mantid Imaging is running correctly, you can ignore this warning. However, if you are experiencing issues with CUDA-based algorithms such as PDHG, you may need to set the CUDA_PATH environment variable to the path where the CUDA Toolkit is installed. Instructions for setting environment variables can be found below under the  :ref:`ImportError: DLL load failed while importing astra_c <importerror-dll-load-failed-while-importing-astra_c-the-specified-module-could-not-be-found>` section.

.. _importerror-dll-load-failed-while-importing-astra_c-the-specified-module-could-not-be-found:

ImportError: DLL load failed while importing astra_c: The specified module could not be found
---------------------------------------------------------------------------------------------

This error usually means that :code:`astra-toolbox` is not installed correctly or the CUDA Runtime libraries are missing.

By default, the CUDA-version of :code:`astra-toolbox` is installed during environment setup, **HOWEVER** it is possible for the incorrect version to be installed for non-NVIDIA GPUs or for machines without a GPU. You can check which version is installed by running the command :code:`mamba list astra-toolbox` in a terminal and verifying that the version installed is the python or cuda version of the package. If the CUDA-version is installed, but you do not have a compatible GPU or the CUDA Runtime libraries installed, you will likely encounter this error.

If you are still experiencing this error after verifying that you have a compatible GPU and the CUDA Runtime libraries installed, it is possible that the `CUDA Toolkit 12.9 <https://developer.nvidia.com/cuda-downloads?target_os=Windows&target_arch=x86_64&target_version=11&target_type=exe_network>`_ is not installed correctly or the environment variable  :code:`CUDA_PATH` is not set correctly.

You can check if Windows can find your CUDA device drivers are present by opening a terminal and entering the command:  :code:`nvidia-smi` you should see an  output similar to the following:

.. table:: Example output from nvidia-smi

   +-----------------------------------------------------------------------------------------+
   | NVIDIA-SMI 576.57                 Driver Version: 576.57         CUDA Version: 12.9     |
   +-----------------------------------------+------------------------+----------------------+
   | GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
   | Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
   |                                         |                        |               MIG M. |
   +=========================================+========================+======================+
   |   0  NVIDIA GeForce GTX 1080 Ti   WDDM  |   00000000:9E:00.0 Off |                  N/A |
   | 20%   29C    P8             15W /  250W |     502MiB /  11264MiB |      3%      Default |
   |                                         |                        |                  N/A |
   +-----------------------------------------+------------------------+----------------------+

**Common causes include:**

- When the CUDA-version of :code:`astra-toolbox` is installed on a machine that does not have a GPU.
- When the Python-version of :code:`astra-toolbox` is installed on a machine that has a GPU but does not have the correct CUDA Runtime libraries installed.
- Possibly after upgrading from Windows 10 to Windows 11, where the CUDA device drivers are not compatible with the new OS or have been misplaced or removed.

**Troubleshooting Steps**

1. **Check for a CUDA-Compatible GPU**

   - Visit the `NVIDIA CUDA GPUs page <https://developer.nvidia.com/cuda-gpus>`_ to confirm your GPU is compatible.
   - If you do not have a compatible GPU, install the Python-version of :code:`astra-toolbox` instead of the CUDA-version.

2. **Verify astra-toolbox Version**

   - Run :code:`mamba list astra-toolbox` in a terminal.
   - Ensure you have the correct version:  

     - Python-version: :code:`astra-toolbox=2.1*=py310h7b2d6b3_0`  
     - CUDA-version: :code:`astra-toolbox=2.1.*=py310h7b2d6b3_0_cuda105`

   - If the CUDA-version is installed but you lack a compatible GPU or CUDA Runtime libraries, you will encounter this error.

3. **Check CUDA Toolkit Installation and Environment Variable**

   - Run :code:`nvcc --version` in a terminal to check if the CUDA Toolkit is installed and on your PATH.
   - If this fails, reinstall the `CUDA Toolkit 12.9 <https://developer.nvidia.com/cuda-downloads?target_os=Windows&target_arch=x86_64&target_version=11&target_type=exe_network>`_.
   - Set the environment variable ``CUDA_PATH`` to your CUDA installation path (e.g., ``C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.9\bin``):

     1. Use Windows Search to find  and open **"Edit environment variables for your account"** .
     2. Click **"New"** under user variables.
     3. Set the variable name to ``CUDA_PATH`` and the value to your CUDA installation path.
     4. Restart your machine.
     5. Open a new terminal and run :code:`echo %CUDA_PATH%` to confirm.

4. **Rebuild Your Developer Environment**

   - After confirming CUDA is installed and ``CUDA_PATH`` is set, run ``python3 ./setup.py create_dev_env`` to ensure the correct :code:`astra-toolbox` version and CUDA libraries are available.
