import pyqtgraph
from pyqtgraph.Qt import QtGui

import math
import numpy as np
import random

from app.misc._utils import Utils


class StddevGraphBpm():

    def __init__(self, pos, relative_to=None, dock_name=''):
        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            dock_name   = dock_name,
            widget      = QtGui.QWidget(),
        ) 

        # Deviation vs BPM graph
        self.__graph = pyqtgraph.PlotWidget(title='Aim dev-x (bpm)')
        self.__graph.getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.__graph.getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.__graph.setLimits(xMin=0, xMax=1200, yMin=-10, yMax=200)
        self.__graph.setLabel('left', 'deviation', units='σ', unitPrefix='')
        self.__graph.setLabel('bottom', 'bpm', units='1/(60*s)', unitPrefix='')
        self.__graph.addLegend()
        self.__graph.getPlotItem().legend.setBrush(pyqtgraph.mkBrush(53, 54, 70, 150))

        # Deviation marker indicating expected deviation according to set CS
        self.__dev_marker = pyqtgraph.InfiniteLine(angle=0, movable=False, pen=pyqtgraph.mkPen(color=(200, 200, 0, 100), style=pyqtgraph.QtCore.Qt.DashLine))
        self.__graph.addItem(self.__dev_marker, ignoreBounds=True)

        # Interactive region plot to the right to select angle between notes in data
        self.__ang_plot = pyqtgraph.PlotWidget()
        self.__ang_plot.setXRange(-0.5, 0.5)
        self.__ang_plot.setYRange(0, 180)
        self.__ang_plot.getViewBox().setMouseEnabled(x=False, y=False)
        self.__ang_plot.enableAutoRange(axis='x', enable=False)
        self.__ang_plot.enableAutoRange(axis='y', enable=False)
        self.__ang_plot.hideAxis('bottom')
        self.__ang_plot.hideAxis('left')
        self.__ang_plot.showAxis('right')
        self.__ang_plot.setFixedWidth(64)

        # Slider region allowing to select angle between notes
        self.__ang_region = pyqtgraph.LinearRegionItem(values=(0, 10), orientation='horizontal')
        self.__ang_region.setBounds((0, 180))
        self.__ang_region.setRegion((0, 30))
        self.__ang_region.sigRegionChanged.connect(lambda: StddevGraphBpm.__angle_region_event(self))

        # Label for the interactive region plot
        self.__ang_label = QtGui.QLabel('    Angle')
        self.__ang_label.setStyleSheet('background-color: black')

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
        self.__px_region.sigRegionChanged.connect(lambda: StddevGraphBpm.__px_region_event(self))

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
        self.__rot_region.sigRegionChanged.connect(lambda: StddevGraphBpm.__rot_region_event(self))

        # Label for the interactive region plot
        self.__rot_label = QtGui.QLabel('    Rot')
        self.__rot_label.setStyleSheet('background-color: black')

        # Put it all together
        self.__ang_plot.addItem(self.__ang_region)
        self.__px_plot.addItem(self.__px_region)
        self.__rot_plot.addItem(self.__rot_region)

        self.__ang_layout = QtGui.QVBoxLayout()
        self.__ang_layout.setSpacing(0)
        self.__ang_layout.addWidget(self.__ang_plot)
        self.__ang_layout.addWidget(self.__ang_label)

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
        self.__layout.addLayout(self.__ang_layout)
        self.__layout.addLayout(self.__px_layout)
        self.__layout.addLayout(self.__rot_layout)


    def plot_data(self, data):
        if data.shape[0] == 0:
            return

        # Clear plots for redraw
        self.__graph.clearPlots()

        # Select data slices by angle
        ang0, ang1 = self.__ang_region.getRegion()
        ang_select = ((ang0 <= data[:, self.COL_ANGLE]) & (data[:, self.COL_ANGLE] <= ang1))

        # Select data slices by distance
        px0, px1 = self.__px_region.getRegion()
        px_select = ((px0 <= data[:, self.COL_PX]) & (data[:, self.COL_PX] <= px1))

        # Select data slices by rotation
        rot0, rot1 = self.__rot_region.getRegion()
        rot_select = ((rot0 <= data[:, self.COL_ROT]) & (data[:, self.COL_ROT] <= rot1))

        # Draw available rotation points on the plot to the right   
        unique_angs = np.unique(data[:, self.COL_ANGLE])
        self.__ang_plot.clearPlots()
        self.__ang_plot.plot(np.zeros(unique_angs.shape[0]), unique_angs, pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')

        unique_pxs = np.unique(data[:, self.COL_PX])
        self.__px_plot.clearPlots()
        self.__px_plot.plot(np.zeros(unique_pxs.shape[0]), unique_pxs, pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')

        unique_rots = np.unique(data[:, self.COL_ROT])
        self.__rot_plot.clearPlots()
        self.__rot_plot.plot(np.zeros(unique_rots.shape[0]), unique_rots, pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')

        # Selected rotation region has no data. Nothing else to do
        if not any(ang_select & px_select & rot_select):
            return

        # Colored gradient r->g->b multiple plots at different osu!px
        unique_pxs = np.unique(data[rot_select & px_select & ang_select, self.COL_PX])

        px_lut = pyqtgraph.ColorMap(
            np.linspace(min(unique_pxs), max(unique_pxs), 3),
            np.array(
                [
                    [  0, 100, 255, 200],
                    [100, 255, 100, 200],
                    [255, 100, 100, 200],
                ]
            )
        )

        # Main plot - deviation vs BPM
        # Adds a plot for every unique osu!px recorded
        for px in unique_pxs:
            # Extract data
            px_select = (data[:, self.COL_PX] == px)
            data_select = px_select & ang_select & rot_select
            if not any(px_select):
                continue

            # Determine data selected by osu!px
            if self.dev_select == self.DEV_X:
                self.__graph.setTitle('Aim dev-x (bpm)')
                stdevs = data[data_select, self.COL_STDEV_X]
            elif self.dev_select == self.DEV_Y:
                self.__graph.setTitle('Aim dev-y (bpm)')
                stdevs = data[data_select, self.COL_STDEV_Y]
            elif self.dev_select == self.DEV_XY:
                self.__graph.setTitle('Aim dev-xy (bpm)')
                stdevs = (data[data_select, self.COL_STDEV_X]**2 + data[data_select, self.COL_STDEV_Y]**2)**0.5
                
            bpms = data[data_select, self.COL_BPM]
            
            # Average overlapping data points (those that fall on same bpm)
            stdevs = np.asarray([ stdevs[bpms == bpm].mean() for bpm in np.unique(bpms) ])
            bpms = np.unique(bpms)

            # Get sort mapping to make points on line graph connect in proper order
            idx_sort = np.argsort(bpms)
            bpms = bpms[idx_sort]
            stdevs = stdevs[idx_sort]

            # Draw plot
            symbol = random.choice([ 't', 'star', 'o', 'd', 'h', 's', 't1', 'p' ])
            color = px_lut.map(px, 'qcolor')
            
            m, b = Utils.linear_regresion(bpms, stdevs)
            if type(m) == type(None) or type(b) == type(None):
                self.__graph.plot(x=bpms, y=stdevs, symbol=symbol, symbolPen='w', symbolSize=10, pen=color, symbolBrush=color, name=f'{px} osu!px')
                continue

            if self.model_compensation:
                y_model = m*bpms + b
                self.__graph.plot(x=bpms, y=stdevs - y_model, symbol=symbol, symbolPen='w', symbolSize=10, pen=color, symbolBrush=color, name=f'{px} osu!px   σ = {np.std(stdevs - y_model):.2f}  m={m:.5f}  b={b:.2f}')
            else:
                self.__graph.plot(x=bpms, y=stdevs, symbol=symbol, symbolPen='w', symbolSize=10, pen=color, symbolBrush=color, name=f'{px} osu!px')

    
    def __angle_region_event(self):
        # When the selection on angle plot changes, reprocess main graph
        StddevGraphBpm.plot_data(self, self.data)

    def __px_region_event(self):
        # When the selection on distance plot changes, reprocess main graph
        StddevGraphBpm.plot_data(self, self.data)

    def __rot_region_event(self):
        # When the selection on rotation plot changes, reprocess main graph
        StddevGraphBpm.plot_data(self, self.data)


    def set_dev(self, dev):
        self.__dev_marker.setPos(dev)