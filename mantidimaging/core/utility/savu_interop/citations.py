from abc import ABC

import numpy as np


class Citation(ABC):
    __slots__ = ("name", "bibtex", "description", "doi", "endnote")
    name: np.string_
    bibtex: np.string_
    description: np.string_
    doi: np.string_
    endnote: np.string_


class HDF5Citation(Citation):
    name = np.string_("HDF5")
    bibtex = np.string_(
        "@ONLINE{hdf5, \nauthor = {{The HDF Group}}, \ntitle = '{Hierarchical Data Format, version 5}', \nyear = {"
        "1997-2016}, \nnote = {/HDF5/}, \n}")
    description = np.string_('Savu uses parallel HDF5 as a backend.')
    doi = np.string_('Default DOI')
    endnote = np.string_('%0 Journal Article\n%T {Hierarchical Data Format, version 5}\n%A HDF Group\n%D 2014\n')


class MPICitation(Citation):
    name = np.string_("MPI")
    bibtex = np.string_(
        '@article{walker1996mpi, \ntitle={MPI: a standard message passing interface}, \nauthor={Walker, David W and '
        'Dongarra, Jack J}, \njournal={Supercomputer}, \nvolume={12}, \npages={56--68}, \nyear={1996}, \npublisher={'
        'ASFRA BV} \n}')
    description = np.string_('HDF5 uses the Message Passing Interface\nstandard for interprocess communication')
    doi = np.string_('Default DOI')
    endnote = np.string_(
        '%0 Journal Article\n%T MPI: a standard message passing interface\n%A Walker, David W\n%A Dongarra, '
        'Jack J\n%J Supercomputer\n%V 12\n%P 56-68\n%@ 0168-7875\n%D 1996\n%I ASFRA BV\n')


class SavuCitation(Citation):
    name = np.string_("Savu")
    bibtex = np.string_(
        '@article{wadeson2016savu,\ntitle={Savu: A Python-based, MPI Framework for Simultaneous\nProcessing of '
        'Multiple, N-dimensional, Large Tomography\nDatasets},\nauthor={Wadeson, Nicola and Basham, Mark},\njournal={'
        'arXiv preprint arXiv:1610.08015},\nyear={2016}\n}')
    description = np.string_('The Savu framework design is described in this paper.')
    doi = np.string_('Default DOI')
    endnote = np.string_(
        '%0 Journal Article\n%T Savu: A Python-based, MPI Framework for Simultaneous Processing\nof Multiple, '
        'N-dimensional, Large Tomography Datasets\n%A Wadeson, Nicola\n%A Basham, Mark\n%J arXiv preprint '
        'arXiv:1610.08015\n%D 2016')


class MantidImagingCitation(Citation):
    name = np.string_("MantidImaging")
    bibtex = np.string_('')
    description = np.string_('The MantidImaging core package used to generate this process lsit.')
    doi = np.string_('TBD')
    endnote = np.string_('')
