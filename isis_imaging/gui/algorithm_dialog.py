from __future__ import absolute_import, division, print_function

from PyQt5 import Qt

from isis_imaging.core.algorithms import gui_compile_ui
from isis_imaging.gui.main_window.mw_view import MainWindowView


class AlgorithmDialog(Qt.QDialog):
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
            main_window, MainWindowView
        ), "The object passed in for main window is not of the correct type!"

        gui_compile_ui.execute(ui_file, self)

        self.main_window = main_window
        self.accepted.connect(self.accepted_action)
        self.stack_uuids = None
        self.selected_stack = None
        self.execute = None
        self.do_before = None
        self.do_after = None
        self.requested_parameter_name = None

    def request_parameter(self, param):
        if param in ["ROI"]:
            self.requested_parameter_name = param
        else:
            raise ValueError("Invalid parameter")

    def apply_before(self, function):
        """
        Any functions added here will be applied before running the main filter.
        This can store multiple functions. All of the results will be forwarded
        to the function inside apply_after!

        :param function: Function that will be executed.
        """
        self.do_before = function

    def apply_after(self, function):
        """
        Function that will be executed after the main execute function (set via set_execute) is finished.
        The parameters provided will be in this order: (data, all_parameters_returned_from_before)

        :param function: Function that will be executed.
        """
        self.do_after = function

    def _call_partial_first_then_forward_args(self, *args, **kwargs):
        # retrieve the decorated function from the GUI file
        decorated_function = self.partial_execute_function()

        # execute it
        return decorated_function(*args, **kwargs)

    def set_execute(self, partial_execute_function):
        """
        Set the main execute function. Only the data parameter will be passed into it, as the rest are expected to be
        decorated during the creation in the GUI files.

        :param partial_execute_function: Partial function that needs to be executed, and will decorate the execute
                                         function with the parameters that the user has put in the dialog
        """
        self.partial_execute_function = partial_execute_function
        self.execute = self._call_partial_first_then_forward_args

    def accepted_action(self):
        self.selected_stack = self.stack_uuids[self.stackNames.currentIndex()]
        # main window only needs to get the partial
        self.main_window.algorithm_accepted(self.selected_stack, self)

    def update_and_show(self):
        # clear the previous entries from the drop down menu
        self.stackNames.clear()

        # get all the new stacks
        stack_list = self.main_window.stack_list()
        if stack_list:  # run away if no stacks are loaded
            self.stack_uuids, user_friendly_names = zip(*stack_list)
            self.stackNames.addItems(user_friendly_names)
        # show the dialogue with the updated stacks
        self.show()
