from functools import partial
from typing import TYPE_CHECKING, Callable, Dict, Any

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QFormLayout


class BaseFilter:
    filter_name = "Unnamed Filter"
    """
    The base class for filter algorithms, which should extend this class.

    All of this classes methods should be overridden, except params and the func_wrappers, which are optional.
    """

    @staticmethod
    def _filter_func(data, **kwargs):
        """
        Executes the filter algorithm on a given set of image data with the given parameters.
        The body of this function does not need to include pre and post processing steps - these should be
        included in the do_before_func_wrapper and do_after_func_wrapper, respectively.

        :param data: the image data to apply the filter to
        :param kwargs: any additional arguments which the specific filter uses
        :return: the image data after applying the filter
        """
        raise_not_implemented("filter_func")

    @staticmethod
    def execute_wrapper(**kwargs) -> partial:
        raise_not_implemented("execute_wrapper")
        return partial(lambda: None)

    @staticmethod
    def register_gui(form: 'QFormLayout', on_change: Callable) -> Dict[str, Any]:
        """
        Adds any required input widgets to the given form and creates and returns a closure for calling
        _filter_func with the arguments supplied in the inputs

        :param form: the layout to create input widgets in
        :param on_change: the filter view action to be bound to all created inputs
        :return: the widgets bound as kwargs which are needed to call execute_wrapper
        """
        raise_not_implemented("register_gui")
        return {}

    @staticmethod
    def params() -> Dict[str, Any]:
        """
        Any parameters required from the StackVisualizer ie. ROI
        :return: a map of parameters names
        """
        return {}

    @staticmethod
    def do_before_wrapper():
        return lambda _: None

    @staticmethod
    def do_after_wrapper():
        return lambda *_: None

    @staticmethod
    def validate_execute_kwargs(kwargs: Dict[str, Any]) -> bool:
        return True


def raise_not_implemented(function_name):
    raise NotImplementedError(f"Required method '{function_name}' not implemented for filter")
