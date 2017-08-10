from __future__ import absolute_import, division, print_function

from PyQt5 import Qt

from mantidimaging.core.algorithms import gui_compile_ui
from mantidimaging.gui.stack_visualiser.sv_available_parameters import Parameters, PARAMETERS_ERROR_MESSAGE


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

        gui_compile_ui.execute(ui_file, self)

        self.main_window = main_window
        self.accepted.connect(self.accepted_action)
        self.stack_uuids = None
        self.selected_stack = None
        self.execute = None
        self.do_before = None
        self.do_after = None
        self._requested_parameter_name = None
        self._parameters_prepared = False

    @property
    def requested_parameter_name(self):
        return self._requested_parameter_name

    @requested_parameter_name.setter
    def requested_parameter_name(self, value):
        self._requested_parameter_name = value

    def request_parameter(self, parameter):
        if parameter == Parameters.ROI:
            self.requested_parameter_name = parameter
        else:
            raise ValueError(PARAMETERS_ERROR_MESSAGE.format(parameter))

    def apply_before(self, function):
        """
        Any functions added here will be applied before running the main filter.
        The result will be forwarded to the function inside apply_after!

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

    def prepare_execute(self):
        """
        This function will run the filter dialog's decorated function, which will read the parameters through a custom_execute
        function defined in the filter dialog's own _gui declaration.
        """
        # retrieve the decorated function from the GUI file
        decorated_function = self.partial_execute_function()

        assert decorated_function is not None, "After the partial function was executed, " \
                                               "it returned a None! It must return a callable."

        # update the execute function, to the correct one
        self.execute = decorated_function

        self._parameters_prepared = True

    def _check_parameters_prepared(self, *args, **kwargs):
        """
        The purpose of this function is to ensure that the caller has called prepare_execute.

        :param args: This function can receive any parameters, to conform to the interface for the forwarding call
        :param kwargs: This function can receive any parameters, to conform to the interface for the forwarding call
        """
        assert self._parameters_prepared == True, "The function prepare_execute has not been called! " \
                                                  "The execution cannot proceed because the custom_execute " \
                                                  "function will not have been executed, and the parameter " \
                                                  "values will not have been updated."

    def set_execute(self, partial_execute_function):
        """
        Set the main execute function. Only the data parameter will be passed into it, as the rest are expected to be
        decorated during the creation in the GUI files.

        :param partial_execute_function: Partial function that needs to be executed, and will decorate the execute
                                         function with the parameters that the user has put in the dialog
        """
        assert partial_execute_function is not None, "The partial function provided is None! It must be a callable."
        self.partial_execute_function = partial_execute_function

        # Set the execute attribute for the assertion check in the registrator. If this attribute does not exist, i.e.
        # this set_execute function was not called, an assertion will fail during registering.
        self.execute = self._check_parameters_prepared

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
