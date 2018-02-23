from logging import getLogger

from mantidimaging.core.imopr.utility import handle_indices


def sanity_checks(config):
    pass


def execute(sample, flat, dark, config, indices):
    import matplotlib.pyplot as plt

    getLogger(__name__).info("Running IMOPR with action VISUALISE/SHOW")

    if len(indices) == 0:
        show_3d(sample[:])
    elif len(indices) == 1:
        show_image(sample[indices[0]])
    else:
        i1, i2 = handle_indices(indices)
        show_3d(sample[i1:i2])

    plt.show()


text_ref = None


class StackVisualiser(object):
    def __init__(self, cube, axis=0, cmap='Greys_r', block=False, **kwargs):
        import matplotlib.pyplot as plt
        from matplotlib.widgets import Slider, RectangleSelector

        self.cube = cube
        self.axis = axis
        self.cmap = cmap
        self.block = block

        # check dim
        if not cube.ndim == 3:
            raise ValueError("cube should be an ndarray with ndim == 3")

        # generate figure
        self.plt = plt
        self.fig = plt.figure()
        # self.image_axis = plt.subplot(111)
        self.image_axis = self.fig.add_axes([0.125, 0.25, 0.75, 0.735])
        # self.fig.subplots_adjust(left=0.20, bottom=0.20)

        # select first image
        s = [slice(0, 1) if i == axis else slice(None) for i in range(3)]
        im = cube[s].squeeze()

        # display image
        self.image = self.image_axis.imshow(im, cmap=cmap, **kwargs)

        # store the selected region
        self.previous_region = None

        # drawtype is 'box' or 'line' or 'none'
        self.rectangle = RectangleSelector(
            self.image_axis,
            self.line_select_callback,
            drawtype='box',
            useblit=True,
            button=[1, 3],  # don't use middle button
            minspanx=5,
            minspany=5,
            spancoords='pixels',
            interactive=True)
        plt.connect('key_press_event', self.toggle_selector)

        # define slider
        axcolor = 'lightgoldenrodyellow'

        # add the axis for the slider
        self.slider_axis = self.fig.add_axes(
            [0.25, 0.1, 0.5, 0.03], axisbg=axcolor)

        self.slider = Slider(
            self.slider_axis,
            'Slices',
            0,
            cube.shape[axis] - 1,
            valinit=0,
            valfmt='%i')

        self.slider.on_changed(self.update)
        plt.show(block)

    def toggle_selector(self, event):
        getLogger(__name__).debug('Key pressed.')
        if event.key in ['Q', 'q'] and self.rectangle.active:
            getLogger(__name__).info('RectangleSelector deactivated.')
            self.rectangle.set_active(False)
        if event.key in ['A', 'a'] and not self.rectangle.active:
            getLogger(__name__).info('RectangleSelector activated.')
            self.rectangle.set_active(True)

    def line_select_callback(self, eclick, erelease):
        'eclick and erelease are the press and release events'
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        region = "%i %i %i %i" % (x1, y1, x2, y2)
        getLogger(__name__).debug(region)

        if self.previous_region is not None:
            self.previous_region.remove()
            self.previous_region = None

        self.previous_region = self.image_axis.text(1, 1, region)
        self.fig.canvas.draw()

    def update(self, val):
        ind = int(self.slider.val)
        s = [
            slice(ind, ind + 1) if i == self.axis else slice(None)
            for i in range(3)
        ]
        im = self.cube[s].squeeze()
        self.image.set_data(im)
        self.fig.canvas.draw()


def show_3d(cube, axis=0, cmap='Greys_r', block=False, **kwargs):
    StackVisualiser(cube, axis, cmap, block)


def show_image(image, cmap='Greys_r', block=False):
    import matplotlib.pyplot as plt
    plt.imshow(image, cmap=cmap)
    plt.show(block)


def stop_python_exit():
    import matplotlib.pyplot as plt
    plt.show()


class Annotate(object):
    def __init__(self, fig):
        from matplotlib.patches import Rectangle
        self.fig = fig
        self.rect = Rectangle((0, 0), 1, 1)
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)

    def on_press(self, event):
        getLogger(__name__).debug('press')
        self.x0 = event.xdata
        self.y0 = event.ydata

    def on_release(self, event):
        getLogger(__name__).debug('release')
        self.x1 = event.xdata
        self.y1 = event.ydata
        self.rect.set_width(self.x1 - self.x0)
        self.rect.set_height(self.y1 - self.y0)
        self.rect.set_xy((self.x0, self.y0))
        self.fig.canvas.draw()
