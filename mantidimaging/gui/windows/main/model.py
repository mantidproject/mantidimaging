import os
import uuid
from collections import namedtuple
from logging import getLogger
from typing import Dict, List, Optional, Any
from PyQt5.Qt import QDockWidget

from mantidimaging.core.data import Images
from mantidimaging.core.data.dataset import Dataset
from mantidimaging.core.io import loader, saver
from mantidimaging.core.utility.data_containers import LoadingParameters
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView

StackId = namedtuple('StackId', ['id', 'name'])


class MainWindowModel(object):
    def __init__(self):
        super(MainWindowModel, self).__init__()

        self.active_stacks: Dict[uuid.UUID, StackVisualiserView] = {}

    def do_load_stack(self, parameters: LoadingParameters, progress):
        ds = Dataset(loader.load_p(parameters.sample, parameters.dtype, progress))
        ds.sample._is_sinograms = parameters.sinograms
        ds.sample.pixel_size = parameters.pixel_size

        if parameters.sample.log_file:
            ds.sample.log_file = loader.load_log(parameters.sample.log_file)

        if parameters.flat_before:
            ds.flat_before = loader.load_p(parameters.flat_before, parameters.dtype, progress)
            if parameters.flat_before.log_file:
                ds.flat_before.log_file = loader.load_log(parameters.flat_before.log_file)
        if parameters.flat_after:
            ds.flat_after = loader.load_p(parameters.flat_after, parameters.dtype, progress)
            if parameters.flat_after.log_file:
                ds.flat_after.log_file = loader.load_log(parameters.flat_after.log_file)

        if parameters.dark_before:
            ds.dark_before = loader.load_p(parameters.dark_before, parameters.dtype, progress)
        if parameters.dark_after:
            ds.dark_after = loader.load_p(parameters.dark_after, parameters.dtype, progress)

        if parameters.proj_180deg:
            ds.sample.proj180deg = loader.load_p(parameters.proj_180deg, parameters.dtype, progress)

        return ds

    def do_saving(self, stack_uuid, output_dir, name_prefix, image_format, overwrite, pixel_depth, progress):
        svp = self.get_stack_visualiser(stack_uuid).presenter
        filenames = saver.save(svp.images,
                               output_dir=output_dir,
                               name_prefix=name_prefix,
                               overwrite_all=overwrite,
                               out_format=image_format,
                               pixel_depth=pixel_depth,
                               progress=progress)
        svp.images.filenames = filenames
        return True

    def create_name(self, filename):
        """
        Creates a suitable name for a newly loaded stack.
        """
        # Avoid file extensions in names
        filename = os.path.splitext(filename)[0]

        # Avoid duplicate names
        name = filename
        current_names = self._stack_names
        num = 1
        while name in current_names:
            num += 1
            name = f"{filename}_{num}"

        return name

    @property
    def stack_list(self) -> List[StackId]:
        stacks = [StackId(stack_id, widget.windowTitle()) for stack_id, widget in self.active_stacks.items()]
        return sorted(stacks, key=lambda x: x.name)

    @property
    def _stack_names(self) -> List[str]:
        return [stack.name for stack in self.stack_list]

    def add_stack(self, stack_visualiser: StackVisualiserView, dock_widget: 'QDockWidget'):
        stack_visualiser.uuid = uuid.uuid1()
        self.active_stacks[stack_visualiser.uuid] = dock_widget
        getLogger(__name__).debug(f"Active stacks: {self.active_stacks}")

    def get_stack(self, stack_uuid: uuid.UUID) -> StackVisualiserView:
        """
        :param stack_uuid: The unique ID of the stack that will be retrieved.
        :return The QDockWidget that contains the Stack Visualiser.
                For direct access to the Stack Visualiser widget use
                get_stack_visualiser
        """
        return self.active_stacks[stack_uuid]

    def set_images_in_stack(self, stack_uuid: uuid.UUID, images: Images):
        stack = self.active_stacks[stack_uuid]
        if isinstance(stack, QDockWidget):
            stack = stack.widget()

        if not stack.presenter.images == images:
            stack.image_view.clear()
            stack.image_view.setImage(images.data)

            # Free previous images stack before reassignment
            stack.presenter.images.free_memory()
            stack.presenter.images = images

    def get_stack_by_name(self, search_name: str) -> Optional[StackVisualiserView]:
        for stack_id in self.stack_list:
            if stack_id.name == search_name:
                return self.get_stack(stack_id.id)
        return None

    def get_stack_by_images(self, images: Images) -> Optional[StackVisualiserView]:
        for _, dock_widget in self.active_stacks.items():
            sv = dock_widget.widget()
            if images is sv.presenter.images:
                return sv
        raise RuntimeError(f"Did not find stack {images} in active stacks! "
                           f"Active stacks: {self.active_stacks.items()}")

    def get_stack_visualiser(self, stack_uuid: uuid.UUID) -> StackVisualiserView:
        """
        :param stack_uuid: The unique ID of the stack that will be retrieved.
        :return The Stack Visualiser widget that contains the data.
        """
        return self.active_stacks[stack_uuid].widget()

    def get_all_stack_visualisers(self) -> List[StackVisualiserView]:
        return [stack.widget() for stack in self.active_stacks.values()]

    def get_stack_history(self, stack_uuid: uuid.UUID) -> Optional[Dict[str, Any]]:
        return self.get_stack_visualiser(stack_uuid).presenter.images.metadata

    def do_remove_stack(self, stack_uuid: uuid.UUID) -> None:
        """
        Removes the stack from the active_stacks dictionary.

        :param stack_uuid: The unique ID of the stack that will be removed.
        """
        del self.active_stacks[stack_uuid]

    @property
    def have_active_stacks(self) -> bool:
        return len(self.active_stacks) > 0
