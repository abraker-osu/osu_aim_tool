import pyqtgraph
from pyqtgraph import QtCore, QtGui


class MissPlotItem(pyqtgraph.GraphicsObject):

    def __init__(self):
        pyqtgraph.GraphicsObject.__init__(self)
    
        self._data = None
        self._picture = QtGui.QPicture()

        self._px_h = self.pixelHeight()
        self._px_w = self.pixelWidth()


    def setData(self, data):
        self._data = data
        self._cached_bounding = None

        self._px_h = self.pixelHeight()
        self._px_w = self.pixelWidth()

        self.generatePicture()


    def generatePicture(self):
        if type(self._data) == type(None):
            return

        ## pre-computing a QPicture object allows paint() to run much more quickly, 
        ## rather than re-drawing the shapes every time.
        self._picture = QtGui.QPicture()

        painter = QtGui.QPainter(self._picture)
        painter.setPen(pyqtgraph.mkPen(color=(255, 0, 0, 50), width=1))

        vr = self.viewRect()
        for timing in self._data:
            painter.drawLine(QtCore.QPointF(float(timing), vr.bottom()), QtCore.QPointF(float(timing), vr.top()))

        painter.end()
    

    def paint(self, painter, *args):
        painter.drawPicture(0, 0, self._picture)
    

    def boundingRect(self):
        if type(self._data) == type(None):
            return QtCore.QRectF()

        if len(self._data) == 0:
            return QtCore.QRectF()

        if type(self._cached_bounding) == type(None):
            # boundingRect _must_ indicate the entire area that will be drawn on
            # or else we will get artifacts and possibly crashing.
            # (in this case, QPicture does all the work of computing the bouning rect for us)
            self._cached_bounding = QtCore.QRectF(0, -200, max(self._data), 200)

        return self._cached_bounding


    def viewRangeChanged(self):
        """
        Called whenever the view coordinates of the ViewBox containing this item have changed.
        """
        px_h = self.pixelHeight()
        px_w = self.pixelWidth()

        # Without pixel_height the render scales with how the view is zoomed in/out
        if self._px_h != px_h or self._px_w != px_w:
            self._px_h = px_h
            self._px_w = px_w

            self.generatePicture()
