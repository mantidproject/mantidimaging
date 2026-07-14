PyCharm
=======

Overview
--------
This page is aimed at developers who use `PyCharm <https://www.jetbrains.com/pycharm/download/>`_ as their integrated development environment (IDE) for Mantid Imaging development.

It includes:

- Opening the Mantid Imaging project in PyCharm
- Configuring the project interpreter
- Optional save and formatting settings

How-to Guides
=============

How to open and prepare PyCharm for Mantid Imaging development
--------------------------------------------------------------

Prerequisites
~~~~~~~~~~~~~
Before starting, ensure you have:

1. An installed copy of `PyCharm <https://www.jetbrains.com/pycharm/download/>`_
2. A clone of the `Mantid Imaging repository <https://github.com/mantidproject/mantidimaging>`_
3. A configured Mantid Imaging developer environment (see :ref:`getting-started` guide)

Opening the project
~~~~~~~~~~~~~~~~~~~
1. Open PyCharm
2. Click ``Open`` on the welcome screen (or ``File -> Open``)
3. Select your local ``mantidimaging`` source directory

PyCharm will index the project and detect Python files automatically.

.. _selecting-pycharm-python-interpreter:

Selecting the Python interpreter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Open ``File -> Settings`` (Windows/Linux) or ``PyCharm -> Settings`` (macOS)
2. Navigate to ``Project: mantidimaging -> Python Interpreter``
3. Click ``Add Interpreter`` and select the environment that matches your Mantid Imaging developer setup (for example, ``mantidimaging-dev``)
4. Apply the changes

Verify that the selected interpreter is correct by checking the interpreter shown in the status bar and by opening the Python Console in PyCharm.

If you are using Pixi, select the interpreter from the local Pixi environment in ``.pixi/envs/dev``.

How to configure save behavior
------------------------------
PyCharm saves files automatically in most workflows (for example when switching windows or running code). To tune this behavior:

1. Open ``File -> Settings -> Appearance & Behavior -> System Settings``
2. Enable or adjust the save options for your preferred workflow

How to disable auto-format on save
----------------------------------
PyCharm can run formatting actions automatically on save using ``Actions on Save``.

1. Open ``File -> Settings -> Tools -> Actions on Save``
2. Disable actions such as ``Reformat code`` and ``Optimize imports`` if you do not want automatic formatting on save

See Also
========
- :ref:`pycharm_plugins` - A list of required and recommended plugins and settings for PyCharm.
- :ref:`pycharm-keyboard-shortcuts` - Commonly used keyboard shortcuts in PyCharm for efficient coding and navigation.
- :ref:`debugging-python-tests` - A guide on setting up and using the debugger for Python development.
