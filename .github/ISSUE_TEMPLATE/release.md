---

name: Pre-Release Issue Template
about: Should be used when Preparing for a release to make sure no tasks are missed during the build-up for a release
title: 'Mantid Imaging [V.V.V] Pre-Release'
labels: 'Release 🚀'
assignees: ''

---

## Description

As part of preparations for the release of Mantid Imaging version [**VERSION***], the following tasks need to be completed.

## High Priority Bugs
<!-- Make sure any high priority bugs which are found during smoke testing are resolved -->
- [ ] [High priority bugs](https://github.com/mantidproject/mantidimaging/issues?q=is%3Aopen+is%3Aissue+label%3A%22High+Priority%22)

## Version Update PR
<!-- Update version references to version [**VERSION**] in the following locations (Update versions within `docs/release_notes/index.rst` as a separate PR updating release notes - See "Update Release Notes PR"). -->

**PR:**
- [ ] `CITATION.cff`
    - Version: `version: "V.V.V"`
    - Release Date: `date-released: YYYY-MM-DD`
- [ ] `docs/_templates/versioning.html`
    - Version: Under `<h3>{{ _('Versions') }}</h3>`
- [ ] `docs/conf.py`
    - Release Date:
    - Version: `release = 'V.V.V<tag>'` (alpha/beta/rc)
    - Version: `smv_tag_whitelist = r'^(2.3.0|2.4.0|2.5.0|2.6.0|2.7.0)$'`
- [ ] `docs/index.rst`
    - Year: update year within Citation if out of date
    - Version: update version within Citation



## Authors PR (if required)
<!--  Make sure list of authors remains in alphabetical order by surname -->

**PR:**
- [ ] `CITATION.cff`
- [ ] `docs/conf.py`
- [ ] `docs/index.rst`


## Release Notes PR
<!-- Update release notes for new version and format "next" release notes -->

**PR:**
- [ ] Compile Release Notes using the following command `python setup.py release_notes` - Copy output and place in new file `docs/release_notes/<V.V.rst>`
- [ ] Add newest version under "next": `docs/release_notes/index.rst`
- [ ] Delete all release notes within: `docs/release_notes/next/dev-1792-python-310`

## Create Release

- [ ] Create release

## Move IDAaas to Stable Branch

- [ ] IDAaaS (move stable branch)

## Update Versions on Main

- [ ] Versions on main


### Additional Info
<!-- Add any additional information below related to the release which may be useful t ou or the reviewer -->


