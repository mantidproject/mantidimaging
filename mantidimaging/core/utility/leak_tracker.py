# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import gc
import sys
import traceback
import weakref
from types import FunctionType
from typing import NamedTuple, Iterable

from numpy import ndarray


class ItemInfo(NamedTuple):
    ref: weakref.ref
    msg: str
    created: list[str]


def obj_to_string(obj, relative=None) -> str:
    """Shows object type, id and extra info for some classes"""
    extra_info = ""
    if isinstance(obj, dict) and relative is not None:
        keys = {k for k, v in obj.items() if v is relative}
        extra_info += f" keys={keys}"

    try:
        if hasattr(obj, "name"):
            extra_info += f" obj.name={obj.name}"

        if hasattr(obj, "id"):
            extra_info += f" obj.id={obj.id}"
    except RuntimeError as e:
        # Can happen with a deleted QWidget
        extra_info += str(e)

    if isinstance(obj, ndarray):
        extra_info += f" ndarray: {obj.shape} {obj.dtype}"

    if isinstance(obj, FunctionType):
        extra_info += f" function: {obj}"

    return f"{type(obj)} pyid={id(obj)} {extra_info}"


def find_owners(obj, depth: int, path: list[str] | None = None, ignore: set[int] | None = None) -> list[list[str]]:
    """Recursively track though references to objects and return a list of routes"""
    all_routes = []
    if path is None:
        path = [obj_to_string(obj)]
    if ignore is None:
        ignore = set()
    ignore.add(id(sys._getframe()))
    ignore.add(id(path))
    ignore.add(id(obj))

    new_refs = [r for r in gc.get_referrers(obj) if id(r) not in ignore]
    ignore.add(id(new_refs))
    if len(new_refs) == 0:
        all_routes.append(path)
    for owner in new_refs:
        if type(owner).__name__ in ['frame', 'list_iterator']:
            continue
        route = [obj_to_string(owner, obj)] + path
        ignore.add(id(route))
        if depth > 0:
            new_routes = find_owners(owner, depth - 1, route, ignore)
            all_routes.extend(new_routes)
        else:
            all_routes.append(route)

    return all_routes


class LeakTracker:
    """
    Track object to debug why large objects are still referenced.

    All objects of interest should be added in their constructor. The pretty_print() method can be called later, so see
    some information about which of the objects are alive.
    """

    def __init__(self):
        self.tracked_objects = []

    def add(self, item, msg=""):
        created = traceback.format_stack()[:-1]
        item_info = ItemInfo(weakref.ref(item), msg, created)
        self.tracked_objects.append(item_info)

    def clear(self) -> None:
        self.tracked_objects.clear()

    def live_objects(self) -> Iterable[ItemInfo]:
        return (item for item in self.tracked_objects if item.ref() is not None)

    def count(self) -> int:
        return sum(1 for _ in self.live_objects())

    def pretty_print(self, debug_init=False, debug_owners=False, trace_depth=5, output=sys.stdout) -> None:
        for item_info in self.live_objects():
            item = item_info.ref()
            print(" Object:", obj_to_string(item_info.ref()), file=output)
            print(f"  {item_info.msg=}", file=output)
            if debug_init:
                print(" Created at:", file=output)
                for line in item_info.created[-trace_depth:]:
                    print("\t", line.strip(), file=output)
                print(file=output)

            if debug_owners:
                print(" Ownership:", file=output)
                routes = find_owners(item, trace_depth)
                for route in routes:
                    for step in route:
                        print("\t", step, file=output)
                    print(file=output)
            print(file=output)


leak_tracker = LeakTracker()
