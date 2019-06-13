"""
Writes out NXS files for SAVU
"""
import itertools as it
import os
from typing import Type

import h5py
import numpy as np

from mantidimaging.core.utility.savu_interop.citations import Citation, HDF5Citation, SavuCitation, MPICitation, \
    MantidImagingCitation
from mantidimaging.core.utility.savu_interop.nxclasses import NXClasses
from mantidimaging.core.utility.savu_interop.plugin_list import SAVUPluginList


def save(spl: SAVUPluginList, file: str, overwrite=False):
    if ".nxs" != file[-4:]:
        file += ".nxs"

    if os.path.isfile(file) and not overwrite:
        raise ValueError("File exists and will not be overwritten!")

    with h5py.File(file, mode="w") as nxs:
        entry_group = nxs.create_group(spl.ENTRY_PATH)
        entry_group.attrs["NX_class"] = NXClasses.NXentry.value

        framework_group = entry_group.create_group(spl.CITATIONS_PATH)
        framework_group.attrs["NX_class"] = NXClasses.NXcollection.value

        _add_citation_group(framework_group, HDF5Citation)
        _add_citation_group(framework_group, MPICitation)
        _add_citation_group(framework_group, SavuCitation)
        _add_citation_group(framework_group, MantidImagingCitation)

        plugin_group = entry_group.create_group(spl.PLUGIN_PATH)
        plugin_group.attrs["NX_class"] = NXClasses.NXprocess.value

        for idx, plugin in enumerate(it.chain(spl.prepend_plugins, spl.plugins, spl.append_plugins), start=1):
            group_path = f"{spl.PLUGIN_INDEX_FMT.format(idx)}"
            group = plugin_group.create_group(group_path)
            group.attrs["NX_class"] = NXClasses.NXnote.value

            for attr in dir(plugin):
                # the shape=(1,) is needed because SAVU uses [:] to access the data,
                # and that fails to slice it, unless the shape is manually specified
                group.create_dataset(attr, shape=(1,), data=getattr(plugin, attr))


def _add_citation_group(framework_group: h5py.Group, dataclass: Type[Citation]):
    group = framework_group.create_group(dataclass.name)
    group.attrs['NX_class'] = NXClasses.NXcite.value

    group.create_dataset('bibtex', data=np.string_(dataclass.bibtex))
    group.create_dataset('description', data=np.string_(dataclass.description))
    group.create_dataset('doi', data=np.string_(dataclass.doi))
    group.create_dataset('endnote', data=np.string_(dataclass.endnote))


if __name__ == "__main__":
    pl = SAVUPluginList()
    mnuhef = save(pl, "np_str_citations", overwrite=True)
