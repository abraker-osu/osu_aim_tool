import pyqtgraph
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore


class AimGraph():

    # Construct a unit radius circle for a graph
    class HitCircle(QtGui.QGraphicsObject):
        def __init__(self, center=(0.0, 0.0), radius=1.0, pen=pyqtgraph.mkPen(color=(255, 255, 255, 255), width=0.5)):
            QtGui.QGraphicsObject.__init__(self)
            self.center = center
            self.radius = radius
            self.pen = pen


        def boundingRect(self):
            rect = QtCore.QRectF(0, 0, 2*self.radius, 2*self.radius)
            rect.moveCenter(QtCore.QPointF(*self.center))
            return rect


        def paint(self, painter, option, widget):
            painter.setPen(self.pen)
            painter.drawEllipse(self.boundingRect())


    def __init__(self):
        self.win_hits = pyqtgraph.GraphicsLayoutWidget(show=False, title='osu! analyzer hit visualization')
        self.win_hits.setFixedSize(2*140, 2*140 + 32)

        self.plot_hits = self.win_hits.addPlot(title='Hit scatter')
        self.plot_hits.hideAxis('left')
        self.plot_hits.hideAxis('bottom')
        self.plot_hits.setXRange(-70, 70)
        self.plot_hits.setYRange(-70, 70)
        self.plot_hits.getViewBox().setMouseEnabled(x=False, y=False)
        self.plot_hits.enableAutoRange(axis='x', enable=False)
        self.plot_hits.enableAutoRange(axis='y', enable=False)
        
        self.circle_item = AimGraph.HitCircle((0, 0))
        self.plot_hits.addItem(self.circle_item)


    def show(self):
        self.win_hits.show()


    def hide(self):
        self.win_hits.hide()


    def set_cs(self, cs):
        cs_px = (109 - 9*cs)/2
        self.circle_item.radius = cs_px
        self.win_hits.update()


    def plot_data(self, aim_x_offsets, aim_y_offsets):
        self.win_hits.clearPlots()
        self.plot_hits.plot(aim_x_offsets, aim_y_offsets, pen=None, symbol='o', symbolPen=None, symbolSize=5, symbolBrush=(100, 100, 255, 200))

