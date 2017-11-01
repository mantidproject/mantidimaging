from __future__ import absolute_import, division, print_function


class BlockQtSignals(object):

    def __init__(self, q_objects):
        from PyQt5 import Qt
        for obj in q_objects:
            assert isinstance(obj, Qt.QObject), \
                "This class must be used with QObjects"

        self.q_objects = q_objects
        self.previous_values = None

    def __enter__(self):
        self.previous_values = \
            [obj.blockSignals(True) for obj in self.q_objects]

    def __exit__(self, *args):
        for obj, prev in zip(self.q_objects, self.previous_values):
            obj.blockSignals(prev)
