import pyqtgraph
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore

import math
import random
import numpy as np

from app.misc._utils import Utils
from app.misc._select_plot import SelectPlot


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
        
        # Interactive region plot to the right to select bpm of notes in data
        self.__bpm_plot = SelectPlot(
            view_min = 0,   view_max = 500,
            val_min  = 0,   val_max  = 1200,
            init_min = 170, init_max = 190,
            label = 'BPM',
            region_event = lambda: StddevGraphAngle.__bpm_region_event(self),
            mouse_ctrl = True
        )

        # Interactive region plot to the right to select distance between notes in data
        self.__px_plot = SelectPlot(
            view_min = 0,  view_max = 512,
            val_min  = 0,  val_max  = 512,
            init_min = 75, init_max = 125,
            label = 'Dist',
            region_event = lambda: StddevGraphAngle.__px_region_event(self),
            mouse_ctrl = True
        )

        # Interactive region plot to the right to select angle of rotation in data
        self.__rot_plot = SelectPlot(
            view_min = 0,  view_max = 180,
            val_min  = 0,  val_max  = 180,
            init_min = 0,  init_max = 30,
            label = 'Rot',
            region_event = lambda: StddevGraphAngle.__rot_region_event(self)
        )

        # Put it all together
        self.__layout = QtGui.QHBoxLayout(self.graphs[self.__id]['widget'])
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(2)
        self.__layout.addWidget(self.__graph)
        self.__layout.addWidget(self.__bpm_plot)
        self.__layout.addWidget(self.__px_plot)
        self.__layout.addWidget(self.__rot_plot)


    def plot_data(self, data):
        if data.shape[0] == 0:
            return

        # Clear plots for redraw
        self.__graph.clearPlots()

        # Select data slices by bpm
        bpm0, bpm1 = self.__bpm_plot.get_region()
        bpm_select = ((bpm0 <= data[:, self.COL_BPM]) & (data[:, self.COL_BPM] <= bpm1))

        # Select data slices by distance
        px0, px1 = self.__px_plot.get_region()
        px_select = ((px0 <= data[:, self.COL_PX]) & (data[:, self.COL_PX] <= px1))

        # Select data slices by rotation
        rot0, rot1 = self.__rot_plot.get_region()
        rot_select = ((rot0 <= data[:, self.COL_ROT]) & (data[:, self.COL_ROT] <= rot1))

        unique_bpms = np.unique(data[:, self.COL_BPM])
        self.__bpm_plot.plot(unique_bpms)

        unique_pxs = np.unique(data[:, self.COL_PX])
        self.__px_plot.plot(unique_pxs)

        unique_rots = np.unique(data[:, self.COL_ROT])
        self.__rot_plot.plot(unique_rots)

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
            elif self.dev_select == self.DEV_T:
                self.__graph.setTitle('Aim dev-t (angle)')
                stdevs = data[data_select, self.COL_STDEV_T]

            if self.avg_data_points:
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