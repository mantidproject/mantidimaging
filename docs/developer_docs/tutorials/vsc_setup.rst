.. _vsc-setup:

VSCode
=========

Overview
--------
This page is aimed at developers who use `Visual Studio Code <https://code.visualstudio.com/download>`_ (VSCode) as their Integrated development environment (IDE) for Mantid Imaging development.

It includes:

- Configuring VSCode for Python development
- Enabling auto-saving 
- Setting up debugging and test workflows
- Installing recommended extensions
- Commonly used keybindings

How-to Guides
=============

How to open and prepare VSCode for Mantid Imaging development
-------------------------------------------------------------
Prerequisites
~~~~~~~~~~~~~
Before starting, ensure you have:

1. An installed copy of VSCode - `Download here <https://code.visualstudio.com/download>`_
2. A clone of the Mantid Imaging repository - `GitHub link <https://github.com/mantidproject/mantidimaging>`_
3. A configured Mantid Imaging developer environment (See :ref:`getting-started` guide)

Opening the project
~~~~~~~~~~~~~~~~~~~
1. Open VSCode
2. Click File -> Open Folder
3. Navigate to your Mantid Imaging source directory and select it

For code editing you are good to go! You can open any file from the left sidebar and start editing.

Selecting the Python interpreter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Open the Command Palette (Ctrl+Shift+P) and search for "Python: Select Interpreter"
2. Choose the Python environment that corresponds to your Mantid Imaging development setup i.e, ``mantidimaging-dev`` or the path similar to `"...\\AppData\\Local\\miniforge3\\envs\\mantidimaging-dev\\python.exe"`

Verify that the selected interpreter is correct by opening a python file and checking the bottom right corner of VSCode, it should display the name of the selected environment.

How to enable auto-save
-----------------------
VSCode has an auto-saving feature that can be enabled to automatically save changes based on predefined conditions. This can help prevent data loss and ensure that changes are saved regularly without the need for manual intervention.

This built in feature can be enabled by:

1. Open the File -> Preferences -> Settings menu
2. Search for "Auto Save"
3. Select the preferred auto save option. It is recommended to use ``onFocusChange`` as it will save the file whenever the editor loses focus, which can help prevent data loss while working on multiple files.

How to debug Python tests
-------------------------

Prerequisites
~~~~~~~~~~~~~

Ensure the `Python Debugger <https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy>`_ is installed.

Configure the debugger
~~~~~~~~~~~~~~~~~~~~~~

Open the existing ``launch.json`` file through the the file finder and update the ``args`` in ``Python: Pytest``` configuration to specify the tests to run. To enable unit, eyes and system tests, make the following updates::

    "args": [
      "--run-unit-tests",
      "--run-eyes-tests",
      "--run-system-tests",
      "-pno:django",
      "${file}"
    ],

Run the debugger
~~~~~~~~~~~~~~~~

1. Open the test file
2. Set breakpoints beside line numbers
3. Open the Run and Debug sidebar
4. Select ``Python: Pytest``
5. Press the green play button

The debugger will pause execution at breakpoints, allowing variables and execution flow to be inspected.

References
==========

Extensions
----------

All extension can either be installed from the `marketplace <https://marketplace.visualstudio.com/>`_ or by clicking the `Extension Marketplace icon <https://code.visualstudio.com/docs/editor/extension-gallery#_browse-and-install-extensions>`_ on the left sidebar of VSCode.

Required Extensions
~~~~~~~~~~~~~~~~~~~

Python
^^^^^^

.. list-table::
    :widths: 25 75
    :header-rows: 1

    * - Extension
      - Purpose
    * - `Python <https://marketplace.visualstudio.com/items?itemName=ms-python.python>`_
      - The main extension for Python development in VSCode, providing features such as IntelliSense, linting, debugging, and code navigation.
    * - `Python Debugger <https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy>`_
      - Provides integration with the debugpy library, allowing developers to debug Python code directly from VSCode.
    * - `Pylance <https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance>`_
      - A language server for Python, providing enhanced IntelliSense, type checking, and code analysis capabilities.
    * - `Mypy Type Checker <https://marketplace.visualstudio.com/items?itemName=ms-python.mypy-type-checker>`_
      - An extension that integrates the Mypy static type checker into VSCode, allowing developers to identify type-related issues in their Python code.
    * - `Ruff <https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff>`_
      - A Python linter and formatter that helps maintain code quality and consistency.
    * - `Pixi Code <https://marketplace.visualstudio.com/items?itemName=renan-r-santos.pixi-code>`_
      - An extension that integrates Pixi environments with the `Python Environments extension <https://github.com/microsoft/vscode-python-environments>`_.

Recommended Extensions
~~~~~~~~~~~~~~~~~~~~~~

Code Reviews
^^^^^^^^^^^^
.. list-table::
    :widths: 25 75
    :header-rows: 1

    * - Extension
      - Purpose
    * - `GitHub Pull Requests <https://marketplace.visualstudio.com/items?itemName=GitHub.vscode-pull-request-github>`_
      - Allows developers to review and manage GitHub pull requests and issues directly from VSCode.
    * - `GitHub Repositories <https://marketplace.visualstudio.com/items?itemName=GitHub.remotehub>`_
      - Provides seamless integration with GitHub repositories, enabling developers to clone, manage, and interact with their GitHub projects from VSCode.

Markdown and Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. list-table::
    :widths: 25 75
    :header-rows: 1

    * - Extension
      - Purpose
    * - `Markdown Checkboxes <https://marketplace.visualstudio.com/items?itemName=bierner.markdown-checkbox>`_
      - An extension that adds support for checkboxes in Markdown files, allowing developers to create interactive checklists within their documentation.
    * - `Dark Github Markdown Preview <https://marketplace.visualstudio.com/items?itemName=ozaki.markdown-github-dark>`_
      - Provides a dark theme for Markdown preview in VSCode to match Github's dark theme styling.

Navigation and Editing
^^^^^^^^^^^^^^^^^^^^^^
.. list-table::
    :widths: 25 75
    :header-rows: 1

    * - Extension
      - Purpose
    * - `Sort Lines <https://marketplace.visualstudio.com/items?itemName=Tyriar.sort-lines>`_
      - An extension that allows developers to sort lines of code or text in ascending or descending order, helping with code organization and readability.
    * - `Bookmarks <https://marketplace.visualstudio.com/items?itemName=alefragnani.Bookmarks>`_
      - Provides a bookmarking system for code navigation, allowing developers to mark and quickly navigate to important lines of code.

Remote Development
^^^^^^^^^^^^^^^^^^
.. list-table::
    :widths: 25 75
    :header-rows: 1

    * - Extension
      - Purpose
    * - `Remote - SSH <https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh>`_
      - Allows developers to connect to remote machines and develop code as if they were working locally.
    * - `Remote - SSH: Editing Configuration Files <https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh-edit>`_
      - Provides an easy way to edit SSH configuration files directly from VSCode, simplifying the process of managing remote connections.

Keybindings
~~~~~~~~~~~
VSCode provides a wide range of keyboard shortcuts for various actions which can be accessed through the command line (Ctrl+Shift+P) and searching for "Keyboard Shortcuts".

Commonly used keybindings
^^^^^^^^^^^^^^^^^^^^^^^^^
.. list-table::
   :widths: 25 25 25 25
   :header-rows: 1

   * - Function
     - Linux
     - MacOS
     - Windows
   * - Search in Files
     - Ctrl+F
     - ⌘+F
     - Ctrl+F
   * - Command Line
     - Ctrl+Shift+P
     - ⌘+Shift+P
     - Ctrl+Shift+P
   * - Fuzzy File Search
     - Ctrl+P
     - ⌘+P
     - Ctrl+P
   * - Launch
     - F5
     - F5
     - F5
