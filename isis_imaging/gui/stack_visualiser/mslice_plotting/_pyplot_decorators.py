from functools import wraps


def draw_colorbar(gcf, colorbar):
    def draw_colorbar_wrapper(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            function(*args, **kwargs)
            cb = getattr(gcf(), '_colorbar_axes', None)
            if cb:
                colorbar(cax=gcf().get_axes()[1])
            else:
                cb = colorbar()
                gcf()._colorbar_axes = cb
        return wrapper
    return draw_colorbar_wrapper
