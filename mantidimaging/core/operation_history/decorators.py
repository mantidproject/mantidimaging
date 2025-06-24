# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import time
import logging
from functools import wraps
from inspect import signature

LOG = logging.getLogger(__name__)


def log_operation(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__qualname__
        sig = signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        clean_kwargs = {k: '<omitted>' if k in {'progress'} else v for k, v in bound.arguments.items()}

        start_time = time.time()
        LOG.info({"operation": func_name, "status": "started", "params": clean_kwargs, "timestamp": start_time})

        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            LOG.info({
                "operation": func_name,
                "status": "completed",
                "duration": round(end_time - start_time, 2),
                "timestamp": end_time
            })
            return result
        except Exception as e:
            LOG.exception({"operation": func_name, "status": "failed", "error": str(e), "timestamp": time.time()})
            raise

    return wrapper
