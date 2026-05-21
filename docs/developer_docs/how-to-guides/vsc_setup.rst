VSCode
======

Overview
--------
This page is aimed at developers who use `Visual Studio Code <https://code.visualstudio.com/download>`_ (VSCode) as their Integrated development environment (IDE) for Mantid Imaging development.

It includes:

- Configuring VSCode for Python development
- Enabling auto-saving 

How-to Guides
=============

How to open and prepare VSCode for Mantid Imaging development
-------------------------------------------------------------
Prerequisites
~~~~~~~~~~~~~
Before starting, ensure you have:

1. An installed copy of `VSCode <https://code.visualstudio.com/download>`_
2. A clone of the `Mantid Imaging repository <https://github.com/mantidproject/mantidimaging>`_
3. A configured Mantid Imaging developer environment (See :ref:`getting-started` guide)

Opening the project
~~~~~~~~~~~~~~~~~~~
1. Open VSCode
2. Click File -> Open Folder
3. Navigate to your Mantid Imaging source directory and select it

For code editing you are good to go! You can open any file from the left sidebar and start editing.

.. _selecting-python-interpreter:

Selecting the Python interpreter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Open the Command Palette ``Ctrl+Shift+P`` and search for "Python: Select Interpreter"
2. Choose the Python environment that corresponds to your Mantid Imaging development setup i.e, ``mantidimaging-dev`` or the path similar to ``"...\\AppData\\Local\\miniforge3\\envs\\mantidimaging-dev\\python.exe"``

.. figure:: /_static/gifs/select_python_interpreter_light.gif
    :alt: Selecting the Python interpreter in VSCode
    :width: 70%
    :align: center
    :class: only-light

    Selecting the Python interpreter in VSCode

.. figure:: /_static/gifs/select_python_interpreter_dark.gif
    :alt: Selecting the Python interpreter in VSCode
    :width: 70%
    :align: center
    :class: only-dark

    Selecting the Python interpreter in VSCode

Verify that the selected interpreter is correct by opening a python file and checking the bottom right corner of VSCode, it should display the name of the selected environment.

If you are using Pixi, the interpreter may be detected automatically from the `.pixi` folder in the project root. In that case, the Pixi environment will appear as something like:  
   `Python 3.12.12 (dev) ./.pixi/envs/dev/bin/python`  

More details on configuring Pixi with VS Code can be found `here <https://pixi.prefix.dev/latest/integration/editor/vscode/#python-extension>`_.

How to enable auto-save
-----------------------
VSCode has an auto-saving feature that can be enabled to automatically save changes based on predefined conditions. This can help prevent data loss and ensure that changes are saved regularly without the need for manual intervention.

This built in feature can be enabled by:

1. Open the File -> Preferences -> Settings menu
2. Search for "Auto Save"
3. Select the preferred auto save option. It is recommended to use ``onFocusChange`` as it will save the file whenever the editor loses focus, which can help prevent data loss while working on multiple files.

.. figure:: /_static/gifs/enable_auto_save_light.gif
    :alt: Enabling auto-save in VSCode
    :width: 70%
    :align: center
    :class: only-light

    Enabling auto-save in VSCode

.. figure:: /_static/gifs/enable_auto_save_dark.gif
    :alt: Enabling auto-save in VSCode
    :width: 70%
    :align: center
    :class: only-dark

    Enabling auto-save in VSCode

See Also
========
- :ref:`vsc_extensions` - A list of required and recommended extensions for VSCode that can enhance the development experience.
- :ref:`vsc-keyboard-shortcuts` - Commonly used keyboard shortcuts in VSCode for efficient coding and navigation.
- :ref:`debugging-python-tests` - A guide on how to set up and use the debugger in VSCode for Python development.