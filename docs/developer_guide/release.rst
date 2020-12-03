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
- Create Git tag from ``master``: ``git tag M.m.p --sign``
- Push the tag to the repository: ``git push M.m.p``
- This should produce a conda package on https://anaconda.org/mantid/mantidimaging that is using the version from the new tag.
  - Edit the labels on this package and add :code:`main`
- (optional) Add release notes in the docs GitHub