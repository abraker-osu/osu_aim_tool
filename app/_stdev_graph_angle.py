import pyqtgraph
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore

import numpy as np


class StddevGraphAngle():

    def __init__(self, pos, relative_to=None, dock_name=''):
        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            dock_name   = dock_name,
            widget      = QtGui.QWidget(),
        )

        # Main graph
        self.__graph = pyqtgraph.PlotWidget(title='Aim dev-x (angle)')
        self.__graph.getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.__graph.getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.__graph.setLimits(xMin=-10, xMax=190, yMin=-10, yMax=200)
        self.__graph.setLabel('left', 'deviation', units='σ', unitPrefix='')
        self.__graph.setLabel('bottom', 'angle', units='deg', unitPrefix='')
        self.__graph.addLegend()

        # Used to set text in legend item
        self.__label_style = pyqtgraph.PlotDataItem(pen=(0,0,0))
        self.__graph.getPlotItem().legend.addItem(self.__label_style, '')
        self.__text = self.__graph.getPlotItem().legend.getLabel(self.__label_style)
        
        # Interactive region plot to the right to select angle of rotation in data
        self.__bpm_plot = pyqtgraph.PlotWidget()
        self.__bpm_plot.setXRange(-0.5, 0.5)
        self.__bpm_plot.setYRange(50, 500)
        self.__bpm_plot.getViewBox().setMouseEnabled(x=False, y=True)
        self.__bpm_plot.setLimits(yMin=-10, yMax=1210)
        self.__bpm_plot.enableAutoRange(axis='x', enable=False)
        self.__bpm_plot.enableAutoRange(axis='y', enable=False)
        self.__bpm_plot.hideAxis('bottom')
        self.__bpm_plot.hideAxis('left')
        self.__bpm_plot.showAxis('right')
        self.__bpm_plot.setFixedWidth(64)

        # Slider region allowing to select bpm
        self.__bpm_region = pyqtgraph.LinearRegionItem(values=(0, 10), orientation='horizontal')
        self.__bpm_region.setBounds((0, 1200))
        self.__bpm_region.setRegion((170, 190))
        self.__bpm_region.sigRegionChanged.connect(lambda: StddevGraphAngle.__bpm_region_event(self))

        # Label for the interactive region plot
        self.__bpm_label = QtGui.QLabel('    BPM')
        self.__bpm_label.setStyleSheet('background-color: black')

        # Interactive region plot to the right to select angle between notes in data
        self.__px_plot = pyqtgraph.PlotWidget()
        self.__px_plot.setXRange(-0.5, 0.5)
        self.__px_plot.setYRange(0, 512)
        self.__px_plot.getViewBox().setMouseEnabled(x=False, y=False)
        self.__px_plot.enableAutoRange(axis='x', enable=False)
        self.__px_plot.enableAutoRange(axis='y', enable=False)
        self.__px_plot.hideAxis('bottom')
        self.__px_plot.hideAxis('left')
        self.__px_plot.showAxis('right')
        self.__px_plot.setFixedWidth(64)

        # Slider region allowing to select distance between notes
        self.__px_region = pyqtgraph.LinearRegionItem(values=(0, 10), orientation='horizontal')
        self.__px_region.setBounds((0, 512))
        self.__px_region.setRegion((75, 125))
        self.__px_region.sigRegionChanged.connect(lambda: StddevGraphAngle.__px_region_event(self))

        # Label for the interactive region plot
        self.__px_label = QtGui.QLabel('    Dist')
        self.__px_label.setStyleSheet('background-color: black')

        # Put it all together
        self.__bpm_plot.addItem(self.__bpm_region)
        self.__px_plot.addItem(self.__px_region)
        
        self.__bpm_layout = QtGui.QVBoxLayout()
        self.__bpm_layout.setSpacing(0)
        self.__bpm_layout.addWidget(self.__bpm_plot)
        self.__bpm_layout.addWidget(self.__bpm_label)

        self.__px_layout = QtGui.QVBoxLayout()
        self.__px_layout.setSpacing(0)
        self.__px_layout.addWidget(self.__px_plot)
        self.__px_layout.addWidget(self.__px_label)

        self.__layout = QtGui.QHBoxLayout(self.graphs[self.__id]['widget'])
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(2)
        self.__layout.addWidget(self.__graph)
        self.__layout.addLayout(self.__bpm_layout)
        self.__layout.addLayout(self.__px_layout)


    def plot_data(self, data):
        if data.shape[0] == 0:
            return

        # Select data slices by bpm
        bpm0, bpm1 = self.__bpm_region.getRegion()
        bpm_select = ((bpm0 <= data[:, self.COL_BPM]) & (data[:, self.COL_BPM] <= bpm1))

        unique_bpms = np.unique(data[:, self.COL_BPM])
        self.__bpm_plot.clearPlots()
        self.__bpm_plot.plot(np.zeros(unique_bpms.shape[0]), unique_bpms, pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')

        # Select data slices by distance
        px0, px1 = self.__px_region.getRegion()
        px_select = ((px0 <= data[:, self.COL_PX]) & (data[:, self.COL_PX] <= px1))

        unique_pxs = np.unique(data[:, self.COL_PX])
        self.__px_plot.clearPlots()
        self.__px_plot.plot(np.zeros(unique_pxs.shape[0]), unique_pxs, pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')

        # Extract relavent data
        stdevs = data[bpm_select & px_select, self.COL_STDEV_X]
        angles = data[bpm_select & px_select, self.COL_ANGLE]

        # Clear plots for redraw
        self.__graph.clearPlots()

        # Draw data plot
        self.__graph.plot(x=angles, y=stdevs, pen=None, symbol='o', symbolPen=None, symbolSize=10, symbolBrush=(100, 100, 255, 200))


    def __bpm_region_event(self):
        StddevGraphAngle.plot_data(self, self.data)

    
    def __px_region_event(self):
        StddevGraphAngle.plot_data(self, self.data)