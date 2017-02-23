from __future__ import (absolute_import, division, print_function)

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from PyQt4 import QtGui
from matplotlib.widgets import Slider
from matplotlib.widgets import RectangleSelector
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np


class StackVisualiser(FigureCanvas):
    def __init__(self,
                 parent,
                 cube,
                 axis=0,
                 cmap='Greys_r',
                 block=False,
                 **kwargs):
        # check dim
        if not cube.ndim == 3:
            raise ValueError("cube should be an ndarray with ndim == 3")

        width = 15
        height = 15
        dpi = 80
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        # self.fig.set_size_inches(5, 5, forward=True)
        super(StackVisualiser, self).__init__(self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.cube = cube
        self.axis = axis
        self.cmap = cmap
        self.block = block
        self.current_image_slice = 0

        # this is the positioning of the rectangle for the images
        self.image_axis = self.fig.add_axes([0.125, 0.25, 0.75, 0.735])

        # select first image
        s = [slice(0, 1) if i == axis else slice(None) for i in range(3)]
        im = cube[s].squeeze()

        self.hist_axis = self.fig.add_axes([0.053, 0.75, 0.2, 0.2])

        # display image
        self.image = self.image_axis.imshow(im, cmap=cmap, **kwargs)

        # store the selected region
        # self.previous_region = None
        self.rectangle = self.createRectangleSelector()

        # not particularly interested in that for now
        # self.fig.canvas.mpl_connect('key_press_event', self.toggle_selector)

        # define slider
        axcolor = 'lightgoldenrodyellow'

        # add the axis for the slider
        self.slider_axis = self.fig.add_axes(
            [0.25, 0.1, 0.5, 0.03], axisbg=axcolor)

        # initialise the actual slider
        self.slider = Slider(
            self.slider_axis,
            'Slices',
            0,
            cube.shape[axis] - 1,
            valinit=0,
            valfmt='%i')
        self.slider.on_changed(self.update_image)

    def createRectangleSelector(self):
        # drawtype is 'box' or 'line' or 'none'
        return RectangleSelector(
            self.image_axis,
            self.line_select_callback,
            drawtype='box',
            useblit=True,
            button=[1, 3],  # don't use middle button
            minspanx=5,
            minspany=5,
            spancoords='pixels',
            interactive=True)

    def toggle_selector(self, event):
        print(' Key pressed.')
        if event.key in ['Q', 'q'] and self.rectangle.active:
            print(' RectangleSelector deactivated.')
            self.rectangle.set_active(False)
        if event.key in ['A', 'a'] and not self.rectangle.active:
            print(' RectangleSelector activated.')
            self.rectangle.set_active(True)

    def line_select_callback(self, eclick, erelease):
        'eclick and erelease are the press and release events'
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        region = "%i %i %i %i" % (x1, y1, x2, y2)
        print(region)

        # if self.previous_region is not None:
        #     self.previous_region.remove()
        #     self.previous_region = None

        # self.previous_region = self.image_axis.text(1, 1, region)
        self.fig.canvas.draw()

    def update_image(self, val):
        """
        If the name of this is changed to just update, 
        it causes an internal error with the matplotlib backend implementation!
        """
        ind = int(self.slider.val)
        print("setting image to", ind)
        self.current_image_slice = ind
        s = [
            slice(ind, ind + 1) if i == self.axis else slice(None)
            for i in range(3)
        ]

        import time
        im = self.cube[s].squeeze()
        s1 = time.time()
        self.image.set_data(im)
        e1 = time.time()
        self.fig.canvas.draw()
        print("Time to set+draw the image", e1 - s1)
        # update the histogram
        # hist_to_be, bin_edges = np.histogram(im)
        s4 = time.time()
        s2 = time.time()
        self.hist_axis.cla()
        e2 = time.time()

        s3 = time.time()
        self.hist_axis.hist(im.flatten(), bins=256)
        e3 = time.time()
        e4 = time.time()
        print("Time to clear the hist axis", e2 - s2)
        print("Time to calc + show the new hist", e3 - s3)
        print("Time to clear + calc + show the hist", e4 - s4)


def show_3d(cube, axis=0, cmap='Greys_r', block=False, **kwargs):
    s = StackVisualiser(cube, axis, cmap, block)
