GitHub Pages setup
==================

The documents are written in RST and generated with Sphinx, then the source is
copied over to the root so that GitHub can display it at
https://mantidproject.github.io/mantidimaging

The source needs to be built inside the `docs` folder (where the
:code:`Makefile` is) with :code:`make html` and then the HTML files will be
generated in a :code:`build` folder.

The most recent release of Sphinx can be installed from PyPI via :code:`pip
install sphinx` (the version available via the Ubuntu repositories does not
include all extensions that are required to build the documentation).
