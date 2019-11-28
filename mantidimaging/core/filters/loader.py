from typing import List

from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.utility.registrator import get_package_children, import_items


def load_filter_packages(package_name="mantidimaging.core.filters", ignored_packages=None) -> List[BaseFilter]:
    """
    Imports all subpackages with a FILTER_CLASS attribute, which should be an extension of BaseFilter.

    These classes are then used to provide the names, required inputs, and behaviour to execute
    then named filter on a stack of images.

    :param package_name: Name of the root package in which to search for
                         filters
    :param ignored_packages: List of ignore rules
    """
    filter_packages = get_package_children(package_name, packages=True, ignore=ignored_packages)
    filter_package_names = [p.name for p in filter_packages]
    loaded_filters = import_items(filter_package_names, required_attributes=['FILTER_CLASS'])
    loaded_filters = filter(lambda f: f.available() if hasattr(f, 'available') else True, loaded_filters)

    return [f.FILTER_CLASS for f in loaded_filters]
