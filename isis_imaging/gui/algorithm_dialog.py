from __future__ import absolute_import, division, print_function

from PyQt4 import QtGui

from isis_imaging.core.algorithms import gui_compile_ui
from gui.main_window.mw_view import ImgpyMainWindowView


class AlgorithmDialog(QtGui.QDialog):
    def __init__(self, main_window, ui_file='gui/ui/alg_dialog.ui'):
        """
        This AlgorithmDialog sets up the backend for the Algorithm dialog handling.
        The front end needs to be created by the filter creator, after the AlgorithmDialog is created.

        This makes it possible to change the design by passing a ui file.

        :param main_window: A reference to the main window, the reason for this is to be able to
                            correctly connect and execute the accepted signal
        :param ui_file: An option to specify custom .ui file if the a custom design is wanted
        """
        super(AlgorithmDialog, self).__init__()
        assert isinstance(
            main_window, ImgpyMainWindowView
        ), "The main window passed in is not of the correct type!"
        gui_compile_ui.execute(ui_file, self)

        self.main_window = main_window
        self.accepted.connect(self.accepted_action)
        self.stack_uuids = None
        self.selected_stack = None

    def accepted_action(self):
        self.selected_stack = self.stack_uuids[self.stackNames.currentIndex()]
        decorated_func = self.decorate_execute()
        # TODO how to tell main from which dialogue we're returning?
        # main window only needs to get the partial tho
        self.main_window.algorithm_accepted(self.selected_stack,
                                            decorated_func)

    def update_and_show(self):
        # clear the drop down menu
        self.stackNames.clear(),

        # get all the new stacks
        stack_list = self.main_window.stack_list()
        if stack_list:  # run away if no stacks are loaded
            self.stack_uuids, user_friendly_names = zip(*stack_list)
            self.stackNames.addItems(user_friendly_names)
        # show the dialogue with the updated stacks
        self.show()

    def decorate_execute(self):
        raise NotImplementedError(
            "This function must be implemented by the AlgorithmDialog creator")
