.. GH Pages setup master file
   See http://sphinx-doc.org/tutorial.html#defining-document-structure

.. GH Pages setup contents:

==================
GitHub Pages setup
==================

The GitHub Pages approach follows the https://github.com/mantidproject/mslice
approach. The documents are written in RST and generated with Sphinx, then the
source is copied over to the root so that GitHub can display it at
https://mantidproject.github.io/mantidimaging

The source is hosted on a different branch -> `git checkout gh-pages`, which
does NOT have the source files. If in the future documentation of the source
will be generated, the source files will have to be merged with these docs.

The source needs to be built inside the `docs` folder (where the `Makefile` is)
with `make html` and then the HTML files will be generated in a `build` folder.

The most recent release of Sphinx can be installed from PyPI via `pip install
sphinx` (the version available via the Ubuntu repositories does not include all
extensions that are required to build the documentation).

The generated files need to be copied to the root directory for GitHub to
display. This needs to be done after every change in order to be reflected in
the `github.io` website.
