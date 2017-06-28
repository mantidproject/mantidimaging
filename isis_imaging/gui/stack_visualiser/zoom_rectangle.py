from __future__ import absolute_import, division, print_function

import PyQt5.QtCore as QCore
import PyQt5.QtGui as QGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg


class FigureCanvasColouredRectangle(FigureCanvasQTAgg):
    """
    From http://stackoverflow.com/questions/28599068/changing-the-edge-color-of-zoom-rect-in-matplotlib
    Subclassing to change the paint event hosted in matplotlib.backends.backend_qt5agg.
    Removed all comments for sake of brevity.
    Paintcolor can be set by settings canvas.rectanglecolor to a QColor.
    """

    def paintEvent(self, e):
        paintcolor = QCore.Qt.black if not hasattr(
            self, "rectanglecolor") else self.rectanglecolor
        if not hasattr(self, 'renderer'):
            return
        if self.blitbox is None:
            if QCore.QSysInfo.ByteOrder == QCore.QSysInfo.LittleEndian:
                stringBuffer = self.renderer._renderer.tostring_bgra()
            else:
                stringBuffer = self.renderer._renderer.tostring_argb()
            qImage = QGui.QImage(stringBuffer, self.renderer.width,
                                 self.renderer.height,
                                 QGui.QImage.Format_ARGB32)
            rect = qImage.rect()
            p = QGui.QPainter(self)
            p.eraseRect(rect)
            p.drawPixmap(QCore.QPoint(0, 0), QGui.QPixmap.fromImage(qImage))
            if self._drawRect is not None:
                p.setPen(QGui.QPen(paintcolor, 1, QCore.Qt.DotLine))
                x, y, w, h = self._drawRect
                p.drawRect(x, y, w, h)
            p.end()
            del qImage

        else:
            bbox = self.blitbox
            l, b, r, t = bbox.extents
            w = int(r) - int(l)
            h = int(t) - int(b)
            t = int(b) + h
            reg = self.copy_from_bbox(bbox)
            stringBuffer = reg.to_string_argb()
            qImage = QGui.QImage(stringBuffer, w, h, QGui.QImage.Format_ARGB32)
            self.blitbox = None
