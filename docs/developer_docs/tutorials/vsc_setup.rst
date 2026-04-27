.. _vsc-setup:

VSCode
=========

Introduction
------------
This is a guide aimed for developers who use Visual Studio Code (VSCode) as their Integrated development environment (IDE) for Mantid Imaging development.
It covers configuring VSCode for Python development, installing recommended extensions, setting up debugging and test workflows, and using features for efficient code navigation, editing, and development.

Prerequisites
-------------
- An installed copy of VSCode - `Download here <https://code.visualstudio.com/download>`_
- A clone of the Mantid Imaging repository - `GitHub link <https://github.com/mantidproject/mantidimaging>`_
- Follow the instructions in the :ref:`getting-started` tutorial to set up the development environment and install dependencies.

How to get Started
------------------
- Run VSCode
- Click File -> Open Folder
- Navigate to your Mantid Imaging source directory and select it
- Install the required extensions for VSCode (see next section)
- For code editing you are good to go! You can open any file from the left sidebar and start editing.

Extensions
----------
All extensions have been tested working on Windows, however most, if not all, extensions should be cross-platform compatible.

Install extensions either by running the commands given on the `marketplace <https://marketplace.visualstudio.com/>`_ or 
by clicking the `Extension Marketplace icon <https://code.visualstudio.com/docs/editor/extension-gallery#_browse-and-install-extensions>`_ on the left sidebar of VSCode.

Required Extensions
---------------------
- `Python <https://marketplace.visualstudio.com/items?itemName=ms-python.python>`_
  - Required to run any Python code and use the Python environment. Most of the python related features are automatically enabled once this extension is installed, but its good to double check against the list in the following section. 

Recommended Extensions
----------------------
Code Reviews
~~~~~~~~~~~~
- `GitHub Pull Requests <https://marketplace.visualstudio.com/items?itemName=GitHub.vscode-pull-request-github>`_ - Allows developers to review and manage GitHub pull requests and issues directly from VSCode.
- `GitHub Repositories <https://marketplace.visualstudio.com/items?itemName=GitHub.remotehub>`_ - Provides seamless integration with GitHub repositories, enabling developers to clone, manage, and interact with their GitHub projects from VSCode.

Python
~~~~~~
- `Python <https://marketplace.visualstudio.com/items?itemName=ms-python.python>`_ - Provides rich support for Python development, including features such as IntelliSense (Pylance), debugging (Python Debugger), and code navigation.
- `Python Debugger <https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy>`_ - An  extension for debugging Python code, allowing developers to set breakpoints, inspect variables, and step through code execution.
- `Pylance <https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance>`_ - A language server for Python, providing enhanced IntelliSense, type checking, and code analysis capabilities.
- `Mypy Type Checker <https://marketplace.visualstudio.com/items?itemName=ms-python.mypy-type-checker>`_ - An extension that integrates the Mypy static type checker into VSCode, allowing developers to identify type-related issues in their Python code.
- `Ruff <https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff>`_ - A Python linter and formatter that helps maintain code quality and consistency.
- `Jupyter Keymap <https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter-keymap>`_ - Provides keybindings for Jupyter Notebook users, making it easier to work with Jupyter Notebooks in VSCode.

Markdown and Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~
- `Markdown Checkboxes <https://marketplace.visualstudio.com/items?itemName=bierner.markdown-checkbox>`_ - An extension that adds support for checkboxes in Markdown files, allowing developers to create interactive checklists within their documentation.
- `Dark Github Markdown Preview <https://marketplace.visualstudio.com/items?itemName=ozaki.markdown-github-dark>`_ - Provides a dark theme for Markdown preview in VSCode to match Github's dark theme styling.

Navigation and Editing
~~~~~~~~~~~~~~~~~~~~~~
- `Sort Lines <https://marketplace.visualstudio.com/items?itemName=Tyriar.sort-lines>`_ - An extension that allows developers to sort lines of code or text in ascending or descending order, helping with code organization and readability.
- `Bookmarks <https://marketplace.visualstudio.com/items?itemName=alefragnani.Bookmarks>`_ - Provides a bookmarking system for code navigation, allowing developers to mark and quickly navigate to important lines of code.

Remote Development
~~~~~~~~~~~~~~~~~~
- `Remote - SSH <https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh>`_ - Allows developers to connect to remote machines and develop code as if they were working locally.
- `Remote - SSH: Editing Configuration Files <https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh-edit>`_ - Provides an easy way to edit SSH configuration files directly from VSCode, simplifying the process of managing remote connections.

Auto Saving
-----------
VSCode has an auto-saving feature that can be enabled to automatically save changes based on predefined conditions. This can help prevent data loss and ensure that changes are saved regularly without the need for manual intervention.

This built in feature can be enabled by following these steps:

- Open the File -> Preferences -> Settings menu
- Search for "Auto Save"
- Select the preferred auto save option. It is recommended to use :code:`onFocusChange` as it will save the file whenever the editor loses focus, which can help prevent data loss while working on multiple files.

Debugging with Python
---------------------
VSCode can attach to and debug running Python targets using debugpy, providing support for breakpoints, variable inspection, and step-through debugging.

Prerequisites
~~~~~~~~~~~~~~
Before debugging, ensure VSCode is using the correct Python environment by following these steps:

- Open the Command Palette (Ctrl+Shift+P) and search for "Python: Select Interpreter"
- Choose the Python environment that corresponds to your Mantid Imaging development setup i.e, :code:`mantidimaging-dev` or the path similar to `"...\\AppData\\Local\\miniforge3\\envs\\mantidimaging-dev\\python.exe"`
- Verify that the selected interpreter is correct by opening a python file and checking the bottom right corner of VSCode, it should display the name of the selected environment.

Configuring the Debugger
~~~~~~~~~~~~~~~~~~~~~~~~
- Make sure the `Python Debugger` extension is installed (see above for details)
- Open the existing launch.json file through the the file finder and update the "args" in :code:`Python: Pytest` configuration to specify the tests to run. To enable eyes and system tests, the args should be updated to::

    "args": [
      "--run-eyes-tests",
      "--run-system-tests",
      "-pno:django",
      "${file}"
    ],

Running the Debugger
~~~~~~~~~~~~~~~~~~~~
- Set breakpoints in the code by clicking in the gutter next to the line numbers where the execution should pause.
- Open the Run and Debug view by clicking on the Run icon in the left sidebar or pressing Ctrl+Shift+D.
- Select the "Python: Pytest" configuration from the dropdown menu at the top of the Run and Debug view.
- Select the file you want to debug and click the green play button to start debugging. The debugger will attach to the running pytest process and pause execution at the set breakpoints, allowing you to inspect variables, step through code, and analyze behavior.

Keybindings
-----------
VSCode provides a wide range of keyboard shortcuts for various actions which can be accessed through the command line (Ctrl+Shift+P) and searching for "Keyboard Shortcuts".

Commonly used keybindings
~~~~~~~~~~~~~~~~~~~~~~~~~
.. list-table::
   :widths: 40 20 20 20
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
