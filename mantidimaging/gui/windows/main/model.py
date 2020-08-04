import os
import uuid
from collections import namedtuple
from logging import getLogger
from typing import Dict, List, Optional, TYPE_CHECKING, Any

from mantidimaging.core.io import loader, saver
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView

if TYPE_CHECKING:
    from PyQt5.Qt import QDockWidget

StackId = namedtuple('StackId', ['id', 'name'])


class MainWindowModel(object):
    def __init__(self):
        super(MainWindowModel, self).__init__()

        self.active_stacks: Dict[uuid.UUID, StackVisualiserView] = {}

    def do_load_stack(self,
                      sample_path,
                      image_format,
                      indices,
                      progress,
                      in_prefix,
                      dtype,
                      flat_path=None,
                      dark_path=None,
                      sinograms=False):
        dataset = loader.load(sample_path,
                              flat_path,
                              dark_path,
                              in_prefix,
                              image_format,
                              dtype,
                              indices=indices,
                              progress=progress)
        dataset.sample._is_sinograms = sinograms
        return dataset

    def do_saving(self, stack_uuid, output_dir, name_prefix, image_format, overwrite, progress):
        svp = self.get_stack_visualiser(stack_uuid).presenter
        filenames = saver.save(svp.images,
                               output_dir=output_dir,
                               name_prefix=name_prefix,
                               overwrite_all=overwrite,
                               out_format=image_format,
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
        current_names = self.stack_names
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
    def stack_names(self) -> List[str]:
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

    def get_stack_by_name(self, search_name: str) -> Optional[StackVisualiserView]:
        for stack_id in self.stack_list:
            if stack_id.name == search_name:
                return self.get_stack(stack_id.id)
        return None

    def get_stack_visualiser(self, stack_uuid: uuid.UUID) -> StackVisualiserView:
        """
        :param stack_uuid: The unique ID of the stack that will be retrieved.
        :return The Stack Visualiser widget that contains the data.
        """
        return self.active_stacks[stack_uuid].widget()

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
