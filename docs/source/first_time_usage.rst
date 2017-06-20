.. First Time users master file
   See http://sphinx-doc.org/tutorial.html#defining-document-structure

.. first_time_usage contents:

=================
 First Time Usage
=================

----------------------
Installing the package
----------------------

**It is recommended that the package is installed in the User's Home directory.**


^^^^^^^^^^^^^^^^^^^^^^
Cloning the repository
^^^^^^^^^^^^^^^^^^^^^^

Requires `git` installed. For instructions on how to install `git` on your Linux distribution please visit `this webpage <https://git-scm.com/download/linux>`_.

""""""
HTTPS:
""""""
`git clone https://github.com/mantidproject/isis_imaging.git`

""""
SSH:
""""
`git clone git@github.com:mantidproject/isis_imaging.git`

^^^^^^^^^^^^^^^^^^^^^^^^^^
Downloading the repository
^^^^^^^^^^^^^^^^^^^^^^^^^^
https://github.com/mantidproject/isis_imaging/archive/master.zip

-----------------
Setting up Python 
-----------------

The easiest way to start using this package is to  have installed `Anaconda 2 <https://www.continuum.io/downloads>`_. This way you only need to add the tools which you will be using.

^^^^^^^
Tomopy: 
^^^^^^^

`conda install -c dgursoy tomopy=1.0.1`. 

Link to the page in Anaconda: `Tomopy in Anaconda <https://anaconda.org/dgursoy/tomopy>`_

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Astra Toolbox: (not supported yet)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
`conda install -c astra-toolbox astra-toolbox=1.8`.

Link to the page in Anaconda: `Astra Toolbox in Anaconda <https://anaconda.org/astra-toolbox/astra-toolbox>`_




--------------------
Starting the package
--------------------
- Calling from command line

Starting the package is done through calling the `imgpy.sh` file in the installation folder. This is a shell script so it needs to be called like this:

`. imgpy.sh <args...>` 

or

`sh imgpy.sh <args...>` 

or

`bash imgpy.sh <args...>`

- Using iPython

To start the package and enter iPython use one of these:

`. imgpy-ipython.sh <args...>` 

or

`sh imgpy-ipython.sh <args...>` 

or

`bash imgpy-ipython.sh <args...>`

- Using GUI

To start the GUI use one of these:

`. imgpy-gui.sh <args...>` 

or

`sh imgpy-gui.sh <args...>` 

or

`bash imgpy-gui.sh <args...>`

----------------------------
Global access to the package
----------------------------

If the package is installed in the $HOME directory it can be given access globally using the following commands:

`sudo ln -s $HOME/imgpy/imgpy.sh /usr/local/bin/imgpy`

`sudo ln -s $HOME/imgpy/imgpy-ipython.sh /usr/local/bin/imgpy-ipython`

`sudo ln -s $HOME/imgpy/imgpy-gui.sh /usr/local/bin/imgpy-gui`


-----------------
Printing the help
-----------------

The help can be printed by passing the `-h` flag.

Depending on how you're accessing the package it will be either:

`imgpy -h`

or

`. imgpy.sh -h`

This will print out the whole help, containing each available command line parameter that can be passed.

------------
Loading Data 
------------
