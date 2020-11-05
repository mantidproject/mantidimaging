import unittest
import uuid

from mantidimaging.gui.windows.main.model import StackId
from mantidimaging.gui.windows.main.save_dialog import sort_by_tomo_and_recon, MWSaveDialog
from mantidimaging.test_helpers.start_qapplication import start_qapplication


class SaveDialogTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(SaveDialogTest, self).__init__(*args, **kwargs)

    def test_sort_stack_names_order(self):
        names = ["Dark", "Dark1", "Flat", "Recon", "Tomo"]
        new_names = sorted(names, key=sort_by_tomo_and_recon)

        self.assertEqual("Recon", new_names[0])
        self.assertEqual("Tomo", new_names[1])


@start_qapplication
class SaveDialogQtTest(unittest.TestCase):
    def test_init(self):
        stack_list = [
            StackId(uuid.uuid4(), "Stack 1"),
            StackId(uuid.uuid4(), "Stack 2"),
            StackId(uuid.uuid4(), "Stack 3"),
            StackId(uuid.uuid4(), "Stack Tomo"),
            StackId(uuid.uuid4(), "Stack Recon"),
        ]
        mwsd = MWSaveDialog(None, stack_list)

        # the Recon stack is top choice
        self.assertEqual(mwsd.stack_uuids[0], stack_list[4].id)
        # the Tomo stack is 2nd choice
        self.assertEqual(mwsd.stack_uuids[1], stack_list[3].id)
