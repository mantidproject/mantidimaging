from figuremanager import FigureManager


def script_log(source_module):
    def script_log_deocator(function):
        def wrapper(*args, **kwargs):
            ret = function(*args, **kwargs)
            args = list(map(repr, args))
            for key in kwargs.keys():
                kwargs[key] = repr(kwargs[key])
            current_manager = FigureManager.get_active_figure()
            current_manager.script_log(
                source_module, function.__name__, args, kwargs)
            return ret
        return wrapper
    return script_log_deocator
