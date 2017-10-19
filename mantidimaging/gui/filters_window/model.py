from __future__ import (absolute_import, division, print_function)


class FiltersWindowModel(object):

    def __init__(self):
        super(FiltersWindowModel, self).__init__()
        self.stack_uuids = []

    def get_stack(self, idx):
        if not self.stack_uuids:
            return None

        return None if idx > len(self.stack_uuids) else self.stack_uuids[idx]
