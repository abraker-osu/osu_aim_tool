import numpy as np

import pyqtgraph
from pyqtgraph.Qt import QtGui


class SelectPlot(QtGui.QWidget):

    def __init__(self, view_min, view_max, val_min, val_max, init_min, init_max, label, region_event, mouse_ctrl=False):
        QtGui.QWidget.__init__(self)
        self.setFixedWidth(64)
        
        init_min = max(init_min, val_min)
        init_max = min(init_max, val_max)

        # Interactive region plot to the right to select
        self.__plot = pyqtgraph.PlotWidget()
        self.__plot.setXRange(-0.5, 0.5)
        self.__plot.setYRange(view_min, view_max)
        self.__plot.setLimits(yMin=val_min - 10, yMax=val_max + 10)
        self.__plot.getViewBox().setMouseEnabled(x=False, y=mouse_ctrl)
        self.__plot.enableAutoRange(axis='x', enable=False)
        self.__plot.enableAutoRange(axis='y', enable=False)
        self.__plot.hideAxis('bottom')
        self.__plot.hideAxis('left')
        self.__plot.showAxis('right')

        # Slider region allowing to select
        self.__region = pyqtgraph.LinearRegionItem(values=(0, 10), orientation='horizontal')
        self.__region.setBounds((val_min, val_max))
        self.__region.setRegion((init_min, init_max))
        self.__region.sigRegionChanged.connect(region_event)

        # Label for the interactive region plot
        self.__label = QtGui.QLabel(f'    {label}')
        self.__label.setStyleSheet('background-color: black')

        self.__plot.addItem(self.__region)

        self.__layout = QtGui.QVBoxLayout(self)
        self.__layout.setSpacing(0)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.addWidget(self.__plot)
        self.__layout.addWidget(self.__label)


    def get_region(self):
        return self.__region.getRegion()


    def plot(self, data):
        self.__plot.clearPlots()
        self.__plot.plot(np.zeros(data.shape[0]), data, pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')