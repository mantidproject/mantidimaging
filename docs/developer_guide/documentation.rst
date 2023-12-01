Documentation
=============

The documents are written in RST and generated with Sphinx, the build is
performed via the Sphinx integration with setuptools.

The documentation is version controlled along with the code, therefore it is
beneficial to make relevant changes to the documentation as the code is
modified.


Workflow
--------

TL;DR of building the documentation.

Run the commands:

.. code::

   python setup.py docs

This will create the documentation in the docs/build/html directory.


API Documentation
-----------------

The API documentation must be generated prior to building the documentation.
This is done with the command: :code:`python setup.py docs_api`.

HTML
----

The HTML pages can be built using :code:`python setup.py docs`, which will build
the documentation in :code:`docs/build.html`.

There is a setuptools command configured to deploy the documentation to GitHub
Pages where it will be visible at https://mantidproject.github.io/mantidimaging

This can be done via the command :code:`python setup.py docs_publish`.  This
assumes you are using SSH as your Git push protocol, if you are not you may
specify an alternative remote URL using the :code:`-r` argument.


Release Notes
-------------

Release notes should be continuously updated during developement. Almost all pull requests should have an update to the relevant file and section in :file:`docs/release_notes`

For the current development work, new release notes go in an individual file for each pull request. This prevents merge conflicts that would occur if two PRs directly edited the same release note file. For example the PR fixing issue #1792 by updating Python would have its change note placed in :file:`docs/release_notes/next/dev-1792-python-310`. The content would be a line::

    #1792 : Update python to 3.10

These will be included into the relent section in :file:`docs/release_notes/next.rst`. At release time the notes can be collected up using::

	python setup.py release_notes

and added to the release notes. The individual files can then be deleted.

When fixes are backported to a release branch, they can be added to the notes for that release, in an updates section.

