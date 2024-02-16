# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List, Optional, Any


class EnablePredicate(ABC):

    @abstractmethod
    def __call__(self, history: Optional[dict[str, Any]]) -> bool:
        pass


class LoadedPredicate(EnablePredicate):

    def __call__(self, history: Optional[dict[str, Any]]) -> bool:
        return history is not None


class HistoryPredicate(EnablePredicate):

    def __init__(self, rule: str):
        if ":" not in rule:
            raise ValueError
        self.filter_name = rule.partition(":")[2]

    def __call__(self, history: Optional[dict[str, Any]]) -> bool:
        if history is not None and "operation_history" in history:
            for op in history["operation_history"]:
                if op["name"] == self.filter_name:
                    return True
        return False


class AndPredicate(EnablePredicate):

    def __init__(self, predicates: Iterable[EnablePredicate]):
        self.predicates = predicates

    def __call__(self, history: Optional[dict[str, Any]]) -> bool:
        for predicate in self.predicates:
            if not predicate(history):
                return False
        return True


def EnablePredicateFactory(rules: str) -> EnablePredicate:
    predicates: List[EnablePredicate] = []
    for rule in rules.split(","):
        rule = rule.strip()
        if rule == "loaded":
            predicates.append(LoadedPredicate())
        elif rule.startswith("history"):
            predicates.append(HistoryPredicate(rule))

    return AndPredicate(predicates)
