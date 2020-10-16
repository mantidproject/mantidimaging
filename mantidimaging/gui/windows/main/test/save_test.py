import unittest

from mantidimaging.gui.windows.main.save_dialog import sort_by_tomo_and_recon


class SaveDialogTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(SaveDialogTest, self).__init__(*args, **kwargs)

    def test_sort_stack_names_order(self):
        names = ["Dark", "Dark1", "Flat", "Recon", "Tomo"]
        new_names = sorted(names, key=sort_by_tomo_and_recon)

        self.assertEqual("Recon", new_names[0])
        self.assertEqual("Tomo", new_names[1])
