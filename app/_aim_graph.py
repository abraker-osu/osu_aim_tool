import numpy as np

import pyqtgraph
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore


class AimGraph():

    SCALE = 3.0
    SIZE = 140*SCALE

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
        self.main_widget = QtGui.QWidget()
        self.main_widget.setWindowTitle('Aim visualization')
        self.main_widget.setSizePolicy(QtGui.QSizePolicy.Policy.Maximum, QtGui.QSizePolicy.Policy.Maximum)
        self.main_widget.setMaximumSize(QtCore.QSize(AimGraph.SIZE, AimGraph.SIZE))

        self.main_layout = QtGui.QGridLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(1)
        
        self.win_hits = pyqtgraph.PlotWidget(show=False, title='Hit visualization')
        self.win_hits.setWindowTitle('osu! Aim Tool Hit Visualization')
        self.win_hits.setFixedSize(AimGraph.SIZE, AimGraph.SIZE + 32)

        self.plot_hits = self.win_hits.plot(title='Hit scatter')
        self.win_hits.hideAxis('left')
        self.win_hits.hideAxis('bottom')
        self.win_hits.setXRange(-AimGraph.SIZE/2, AimGraph.SIZE/2)
        self.win_hits.setYRange(-AimGraph.SIZE/2, AimGraph.SIZE/2)
        self.win_hits.getViewBox().setMouseEnabled(x=False, y=False)
        self.win_hits.enableAutoRange(axis='x', enable=False)
        self.win_hits.enableAutoRange(axis='y', enable=False)
        
        self.circle_item = AimGraph.HitCircle((0, 0))
        self.win_hits.addItem(self.circle_item)

        self.dev_x = pyqtgraph.PlotWidget(show=False)
        self.dev_x.getViewBox().setMouseEnabled(x=False, y=False)
        self.dev_x.enableAutoRange(axis='x', enable=False)
        self.dev_x.enableAutoRange(axis='y', enable=True)
        self.dev_x.hideAxis('left')
        self.dev_x.showAxis('bottom')
        self.dev_x.setFixedHeight(64 + 4*AimGraph.SCALE)
        self.dev_x.setXRange(-AimGraph.SIZE/2, AimGraph.SIZE/2)

        self.dev_y = pyqtgraph.PlotWidget(show=False)
        self.dev_y.getViewBox().setMouseEnabled(x=False, y=False)
        self.dev_y.enableAutoRange(axis='x', enable=True)
        self.dev_y.enableAutoRange(axis='y', enable=False)
        self.dev_y.hideAxis('bottom')
        self.dev_y.hideAxis('left')
        self.dev_y.showAxis('right')
        self.dev_y.setFixedWidth(64 + 4*AimGraph.SCALE)
        self.dev_y.setYRange(-AimGraph.SIZE/2, AimGraph.SIZE/2)

        self.main_layout.addWidget(self.win_hits, 0, 0)
        self.main_layout.addWidget(self.dev_x, 1, 0)
        self.main_layout.addWidget(self.dev_y, 0, 1)


    def show(self):
        self.main_widget.show()


    def hide(self):
        self.main_widget.hide()


    def set_cs(self, cs):
        cs_px = (109 - 9*cs)/2
        self.circle_item.radius = cs_px*AimGraph.SCALE
        self.win_hits.update()


    def plot_data(self, aim_x_offsets, aim_y_offsets):
        scaled_aim_x_offsets = aim_x_offsets*AimGraph.SCALE
        scaled_aim_y_offsets = aim_y_offsets*AimGraph.SCALE

        # Plot aim data scatter plot
        self.plot_hits.setData(scaled_aim_x_offsets, scaled_aim_y_offsets, pen=None, symbol='o', symbolPen=None, symbolSize=5, symbolBrush=(100, 100, 255, 200))

        # Plot a histogram for x-dev
        y, x = np.histogram(scaled_aim_x_offsets, bins=np.linspace(-AimGraph.SIZE/2, AimGraph.SIZE/2, int(AimGraph.SIZE/5)))
        self.dev_x.clearPlots()
        self.dev_x.plot(x, y, stepMode='center', fillLevel=0, fillOutline=True, brush=(0, 0, 255, 150))

        # Plot a histogram for y-dev
        y, x = np.histogram(scaled_aim_y_offsets, bins=np.linspace(-AimGraph.SIZE/2, AimGraph.SIZE/2, int(AimGraph.SIZE/5)))
        self.dev_y.clearPlots()
        plot = self.dev_y.plot(x, y, stepMode='center', fillLevel=0, fillOutline=True, brush=(0, 0, 255, 150))
        plot.rotate(90)
