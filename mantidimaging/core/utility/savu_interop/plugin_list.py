from dataclasses import dataclass
from typing import List, Iterable

import numpy as np


@dataclass
class SAVUPluginEntry:
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

    def __init__(self):
        self.prepend_plugins: List[SAVUPluginEntry] = [
            SAVUPluginEntry(active=True,
                            data=np.string_(
                                '{"data_prefix": null, "flat_prefix": null, "dark_prefix": null, "angles": null, '
                                '"frame_dim": 0, "preview": [], "dataset_name": "tomo"}'),
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

        self.plugins: List[SAVUPluginEntry] = []

        self.append_plugins: List[SAVUPluginEntry] = [
            SAVUPluginEntry(active=True,
                            data=np.string_(
                                '{"in_datasets": [], "out_datasets": [], "prefix": null, "pattern": "VOLUME_XZ"}'),
                            desc=np.string_(
                                '{"in_datasets": "The name of the dataset to save.", "out_datasets": "Hidden, '
                                'dummy out_datasets entry.", "prefix": "Override the default output tiff file '
                                'prefix.", "pattern": "How to slice the data."}'),
                            hide=np.string_('["out_datasets"]'),
                            id=np.string_('savu.plugins.savers.tiff_saver'),
                            name=np.string_('TiffSaver'),
                            user=np.string_('[]'))
        ]

    def __len__(self):
        return len(self.prepend_plugins) + len(self.plugins) + len(self.append_plugins)
