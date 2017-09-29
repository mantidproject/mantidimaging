from __future__ import (absolute_import, division, print_function)

from logging import getLogger


class ConsoleProgressBar(object):

    def __init__(self, parent_progress, ascii_bar=False):
        log = getLogger(__name__)

        msg = 'Progress'
        total = parent_progress.end_step

        try:
            from tqdm import tqdm
            self.progress_bar = tqdm(total=total, desc=msg, ascii=ascii_bar)
        except ImportError:
            try:
                from custom_timer import CustomTimer
                self.progress_bar = CustomTimer(total, msg)
            except ImportError:
                self.progress_bar = None
                log.error('Failed to initialise progress bar')

    def close(self):
        self.progress_bar.close()

    def update(self, value):
        self.progress_bar.update(value)
