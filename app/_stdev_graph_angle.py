import pyqtgraph
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore

import math
import random
import numpy as np

from app.misc._utils import Utils


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
        self.__graph.enableAutoRange(axis='x', enable=False)
        self.__graph.enableAutoRange(axis='y', enable=False)
        self.__graph.setLimits(xMin=-10, xMax=190, yMin=-10, yMax=200)
        self.__graph.setRange(xRange=[-10, 190], yRange=[-10, 20])
        self.__graph.setLabel('left', 'deviation', units='σ', unitPrefix='')
        self.__graph.setLabel('bottom', 'angle', units='deg', unitPrefix='')
        self.__graph.addLegend()

        # Deviation marker indicating expected deviation according to set CS
        self.__dev_marker_95 = pyqtgraph.InfiniteLine(angle=0, movable=False, pen=pyqtgraph.mkPen(color=(255, 100, 0, 100), style=pyqtgraph.QtCore.Qt.DashLine))
        self.__graph.addItem(self.__dev_marker_95, ignoreBounds=True)

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
        self.__px_plot.getViewBox().setMouseEnabled(x=False, y=True)
        self.__px_plot.setLimits(yMin=-10, yMax=520)
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

        # Interactive region plot to the right to select angle of rotation in data
        self.__rot_plot = pyqtgraph.PlotWidget()
        self.__rot_plot.setXRange(-0.5, 0.5)
        self.__rot_plot.setYRange(0, 180)
        self.__rot_plot.getViewBox().setMouseEnabled(x=False, y=False)
        self.__rot_plot.enableAutoRange(axis='x', enable=False)
        self.__rot_plot.enableAutoRange(axis='y', enable=False)
        self.__rot_plot.hideAxis('bottom')
        self.__rot_plot.hideAxis('left')
        self.__rot_plot.showAxis('right')
        self.__rot_plot.setFixedWidth(64)

        # Slider region allowing to select angle of rotation
        self.__rot_region = pyqtgraph.LinearRegionItem(values=(0, 10), orientation='horizontal')
        self.__rot_region.setBounds((0, 180))
        self.__rot_region.setRegion((0, 30))
        self.__rot_region.sigRegionChanged.connect(lambda: StddevGraphAngle.__rot_region_event(self))

        # Label for the interactive region plot
        self.__rot_label = QtGui.QLabel('    Rot')
        self.__rot_label.setStyleSheet('background-color: black')

        # Put it all together
        self.__bpm_plot.addItem(self.__bpm_region)
        self.__px_plot.addItem(self.__px_region)
        self.__rot_plot.addItem(self.__rot_region)
        
        self.__bpm_layout = QtGui.QVBoxLayout()
        self.__bpm_layout.setSpacing(0)
        self.__bpm_layout.addWidget(self.__bpm_plot)
        self.__bpm_layout.addWidget(self.__bpm_label)

        self.__px_layout = QtGui.QVBoxLayout()
        self.__px_layout.setSpacing(0)
        self.__px_layout.addWidget(self.__px_plot)
        self.__px_layout.addWidget(self.__px_label)

        self.__rot_layout = QtGui.QVBoxLayout()
        self.__rot_layout.setSpacing(0)
        self.__rot_layout.addWidget(self.__rot_plot)
        self.__rot_layout.addWidget(self.__rot_label)

        self.__layout = QtGui.QHBoxLayout(self.graphs[self.__id]['widget'])
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(2)
        self.__layout.addWidget(self.__graph)
        self.__layout.addLayout(self.__bpm_layout)
        self.__layout.addLayout(self.__px_layout)
        self.__layout.addLayout(self.__rot_layout)


    def plot_data(self, data):
        if data.shape[0] == 0:
            return

        # Clear plots for redraw
        self.__graph.clearPlots()

        # Select data slices by bpm
        bpm0, bpm1 = self.__bpm_region.getRegion()
        bpm_select = ((bpm0 <= data[:, self.COL_BPM]) & (data[:, self.COL_BPM] <= bpm1))

        # Select data slices by distance
        px0, px1 = self.__px_region.getRegion()
        px_select = ((px0 <= data[:, self.COL_PX]) & (data[:, self.COL_PX] <= px1))

        # Select data slices by rotation
        rot0, rot1 = self.__rot_region.getRegion()
        rot_select = ((rot0 <= data[:, self.COL_ROT]) & (data[:, self.COL_ROT] <= rot1))

        unique_bpms = np.unique(data[:, self.COL_BPM])
        self.__bpm_plot.clearPlots()
        self.__bpm_plot.plot(np.zeros(unique_bpms.shape[0]), unique_bpms, pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')

        unique_pxs = np.unique(data[:, self.COL_PX])
        self.__px_plot.clearPlots()
        self.__px_plot.plot(np.zeros(unique_pxs.shape[0]), unique_pxs, pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')

        unique_rots = np.unique(data[:, self.COL_ROT])
        self.__rot_plot.clearPlots()
        self.__rot_plot.plot(np.zeros(unique_rots.shape[0]), unique_rots, pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')

        # Selected rotation region has no data. Nothing else to do
        if not any(bpm_select & px_select & rot_select):
            return

        # Colored gradient r->g->b multiple plots at different osu!px
        unique_bpms = np.unique(data[bpm_select & px_select & rot_select, self.COL_BPM])

        bpm_lut = pyqtgraph.ColorMap(
            np.linspace(min(unique_bpms), max(unique_bpms), 3),
            np.array(
                [
                    [  0, 100, 255, 200],
                    [100, 255, 100, 200],
                    [255, 100, 100, 200],
                ]
            )
        )

        # Main plot - deviation vs osu!px
        # Adds a plot for every unique BPM recorded
        for bpm in unique_bpms:
            # Determine data selected by BPM
            bpm_select = (data[:, self.COL_BPM] == bpm)
            data_select = bpm_select & px_select & rot_select
            if not any(data_select):
                # Selected region has no data. Nothing else to do
                continue

            angles = data[data_select, self.COL_ANGLE]

            # Determine data selected by osu!px
            if self.dev_select == self.DEV_X:
                self.__graph.setTitle('Aim dev-x (angle)')
                stdevs = data[data_select, self.COL_STDEV_X]
            elif self.dev_select == self.DEV_Y:
                self.__graph.setTitle('Aim dev-y (angle)')
                stdevs = data[data_select, self.COL_STDEV_Y]
            elif self.dev_select == self.DEV_XY:
                self.__graph.setTitle('Aim dev-xy (angle)')
                stdevs = (data[data_select, self.COL_STDEV_X]**2 + data[data_select, self.COL_STDEV_Y]**2)**0.5

            # Use best N points for data display
            num_points = min(len(stdevs), self.MAX_NUM_DATA_POINTS)

            # Average overlapping data points (those that fall on same angle)
            stdevs = np.asarray([ np.sort(stdevs[angles == angle])[:num_points].mean() for angle in np.unique(angles) ])
            angles = np.unique(angles)

            # Get sort mapping to make points on line graph connect in proper order
            idx_sort = np.argsort(angles)
            angles = angles[idx_sort]
            stdevs = stdevs[idx_sort]

            # Draw plot
            color = bpm_lut.map(bpm, 'qcolor')

            m, b = Utils.linear_regresion(angles, stdevs)
            if type(m) == type(None) or type(b) == type(None):
                self.__graph.plot(x=angles, y=stdevs, symbol='o', symbolPen=None, symbolSize=5, pen=None, symbolBrush=color, name=f'{bpm} bpm')
                continue

            if self.model_compensation:
                y_model = m*angles + b
                self.__graph.plot(x=angles, y=stdevs - y_model, symbol='o', symbolPen=None, symbolSize=5, pen=None, symbolBrush=color, name=f'{bpm} bpm   σ = {np.std(stdevs - y_model):.2f}  m={m:.5f}  b={b:.2f}')
            else:
                self.__graph.plot(x=angles, y=stdevs, symbol='o', symbolPen=None, symbolSize=5, pen=None, symbolBrush=color, name=f'{bpm} bpm')


    def __bpm_region_event(self):
        # When the selection on bpm plot changes, reprocess main graph
        StddevGraphAngle.plot_data(self, self.data)

    
    def __px_region_event(self):
        # When the selection on distance plot changes, reprocess main graph
        StddevGraphAngle.plot_data(self, self.data)


    def __rot_region_event(self):
        # When the selection on rotation plot changes, reprocess main graph
        StddevGraphAngle.plot_data(self, self.data)


    def set_dev(self, dev):
        self.__dev_marker_95.setPos(dev/4)