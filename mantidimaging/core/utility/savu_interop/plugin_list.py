from dataclasses import dataclass
from typing import List, Iterable

import numpy as np

from mantidimaging.core.utility.savu_interop.citations import Citation


@dataclass
class SAVUParameter:
    __slots__ = ("description", "is_hidden", "is_user", "name", "type", "value")
    description: str
    is_hidden: bool
    is_user: bool
    name: str
    type: str
    value: str


class SAVUPlugin(object):
    __slots__ = ("name", "info", "synopsis", "warn", "id", "citation", "parameters")
    name: str
    info: str
    synopsis: str
    warn: str
    id: str
    citation: Citation
    parameters: List[SAVUParameter]

    def __init__(self, name: str, details: dict):
        self.name = name
        self.info = details["info"]
        self.synopsis = details["synopsis"]
        self.warn = details["warn"]
        self.id = details["id"]
        self.citation = details["citation"]
        self.parameters = []
        for param in details["parameters"]:
            self.parameters.append(SAVUParameter(**param))

    def visible_parameters(self):
        """
        Returns the list of parameters that will be visible in the GUI
        :return:
        """
        for param in self.parameters:
            if not param.is_hidden and \
                    not param.name == "in_datasets" and \
                    not param.name == "out_datasets":
                yield param


@dataclass
class SAVUPluginListEntry:
    """
    This contains a specialised subset of parameters that are put into the process list.
    It does not contain all the data of the plugin.
    """
    active: bool
    data: np.string_
    desc: np.string_
    hide: np.string_
    id: np.string_
    name: np.string_
    user: np.string_

    def __dir__(self) -> Iterable[str]:
        return filter(lambda x: not x.startswith("__"), super().__dir__())


class SAVUPluginList:
    ENTRY_PATH = "entry"
    PLUGIN_PATH = "plugin"
    CITATIONS_PATH = "framework_citations"
    # Savu has these spaces in there, they can't be removed or it won't properly load
    PLUGIN_INDEX_FMT = "   {} "

    def __init__(self, data_prefix, num_images, preview="end"):
        self.prepend_plugins: List[SAVUPluginListEntry] = [
            # preview is in format: [<indices start:end:step>, <rows start:end:step>, <columns start:end:step>]
            SAVUPluginListEntry(active=True,
                                data=np.string_(
                                    f'{{"data_prefix": "{data_prefix}", "flat_prefix": null, "dark_prefix": null, '
                                    f'"angles": "np.linspace(0, 360, {num_images})", '
                                    f'"frame_dim": 0, "preview": "[{preview[0]}:{preview[1]}:{preview[2]}, :, :]",'
                                    f'"dataset_name": "tomo"}}'),
                                desc=np.string_(
                                    '{"data_prefix": "A file prefix for the data file.", "flat_prefix": "A file prefix '
                                    'for the flat field files, including the folder path if different from the data.", '
                                    '"dark_prefix": "A file prefix for the dark field files, including the folder path '
                                    'if different from the data.", "angles": "A python statement to be evaluated (e.g '
                                    'np.linspace(0, 180, nAngles)) or a file.", "frame_dim": "Which dimension requires '
                                    'stitching?", "preview": "A slice list of required frames.", "dataset_name": "The '
                                    'name assigned to the dataset."}'),
                                hide=np.string_('[]'),
                                id=np.string_('savu.plugins.loaders.full_field_loaders.image_loader'),
                                name=np.string_('ImageLoader'),
                                user=np.string_('["preview"]'))]

        self.plugins: List[SAVUPluginListEntry] = []

        self.append_plugins: List[SAVUPluginListEntry] = [
            SAVUPluginListEntry(active=True,
                                data=np.string_(
                                    '{"in_datasets": [], "out_datasets": [], "prefix": null, "pattern": "PROJECTION"}'),
                                desc=np.string_(
                                    '{"in_datasets": "The name of the dataset to save.", "out_datasets": "Hidden, '
                                    'dummy out_datasets entry.", "prefix": "Override the default output tiff file '
                                    'prefix.", "pattern": "How to slice the data."}'),
                                hide=np.string_('["out_datasets"]'),
                                id=np.string_('savu.plugins.savers.tiff_saver'),
                                name=np.string_('TiffSaver'),
                                user=np.string_('[]'))
        ]

    def add_plugin(self, plugin: SAVUPluginListEntry):
        self.plugins.append(plugin)

    def __len__(self):
        return len(self.prepend_plugins) + len(self.plugins) + len(self.append_plugins)

    def __str__(self):
        # -2 trims the trailing comma and space
        return ", ".join([str(x) for x in self.prepend_plugins + self.plugins + self.append_plugins])[:-2]
