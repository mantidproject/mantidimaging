Creating a Release
==================

This is a checklist for creating a new release.

Releases are created from the ``master`` branch.

The version number is expected to be in SemVer format and will be referred to as
``M.m.p``, adjust this as appropriate.

- Update version numbers in:
   - ``setup.py``
   - ``mantidimaging/__init__.py``
   - ``docs/conf.py``
   - Grep for current version in the repository just to make sure you've got them all

Release candidate
-----------------
- Checkout master, and create a release branch ``release-M.m.p``
- Push the branch to the remote
- Create Git tag on the release branch with format ``M.m.prc`` - note the ``rc`` at the end, this marks it as a release candidate
- Push the tag to the repository: ``git push M.m.p``. New executions of ``conda build`` will now use the new tag
- Build the conda package locally, or use the Github action on the release branch
- Publish the package using the ``main`` label, then install it and test that it works OK

Release
-------
- Similar to the release candidate, but tag without the ``rc`` suffix
- Build and publish the package
- Install it and make sure it works
- Delete the RC package from Anaconda.
  - Also consider deleting old unstable packages that are just taking up space.
  - ``main`` version packages should never be deleted