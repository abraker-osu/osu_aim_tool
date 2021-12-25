import pyqtgraph
from pyqtgraph.Qt import QtGui

import math
import numpy as np
import random

from app.misc._utils import MathUtils
from app.misc._select_plot import SelectPlot


class StddevGraphNumNotes():

    def __init__(self, pos, relative_to=None, dock_name=''):
        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            dock_name   = dock_name,
            widget      = QtGui.QWidget(),
        ) 

        # Deviation vs Number of Notes graph
        self.__graph = pyqtgraph.PlotWidget(title='Aim dev-x (# notes)')
        self.__graph.getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.__graph.getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.__graph.enableAutoRange(axis='x', enable=False)
        self.__graph.enableAutoRange(axis='y', enable=False)
        self.__graph.setLimits(xMin=0, xMax=1200, yMin=-10, yMax=200)
        self.__graph.setRange(xRange=[-10, 500], yRange=[-10, 20])
        self.__graph.setLabel('left', 'deviation', units='σ', unitPrefix='')
        self.__graph.setLabel('bottom', '# of notes', units='#', unitPrefix='')
        self.__graph.addLegend()
        self.__graph.getPlotItem().legend.setBrush(pyqtgraph.mkBrush(53, 54, 70, 150))

        # Deviation marker indicating expected deviation according to set CS
        self.__dev_marker_95 = pyqtgraph.InfiniteLine(angle=0, movable=False, pen=pyqtgraph.mkPen(color=(255, 100, 0, 100), style=pyqtgraph.QtCore.Qt.DashLine))
        self.__graph.addItem(self.__dev_marker_95, ignoreBounds=True)

        # Interactive region plot to the right to select angle between notes in data
        self.__ang_plot = SelectPlot(
            view_min = 0, view_max = 180,
            val_min  = 0, val_max  = 180,
            init_min = 0, init_max = 180,
            label = 'Angle',
            region_event = lambda: StddevGraphNumNotes.__angle_region_event(self)
        )

        # Interactive region plot to the right to select distance between notes in data
        self.__px_plot = SelectPlot(
            view_min = 0,  view_max = 512,
            val_min  = 0,  val_max  = 512,
            init_min = 75, init_max = 125,
            label = 'Dist',
            region_event = lambda: StddevGraphNumNotes.__px_region_event(self),
            mouse_ctrl = True
        )

        # Interactive region plot to the right to select bpm of notes in data
        self.__bpm_plot = SelectPlot(
            view_min = 0,   view_max = 500,
            val_min  = 0,   val_max  = 1200,
            init_min = 170, init_max = 190,
            label = 'BPM',
            region_event = lambda: StddevGraphNumNotes.__bpm_region_event(self),
            mouse_ctrl = True
        )

        # Interactive region plot to the right to select angle of rotation in data
        self.__rot_plot = SelectPlot(
            view_min = 0,  view_max = 180,
            val_min  = 0,  val_max  = 180,
            init_min = 0,  init_max = 30,
            label = 'Rot',
            region_event = lambda: StddevGraphNumNotes.__rot_region_event(self)
        )

        # Put it all together
        self.__layout = QtGui.QHBoxLayout(self.graphs[self.__id]['widget'])
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(2)
        self.__layout.addWidget(self.__graph)
        self.__layout.addWidget(self.__ang_plot)
        self.__layout.addWidget(self.__px_plot)
        self.__layout.addWidget(self.__bpm_plot)
        self.__layout.addWidget(self.__rot_plot)


    def plot_data(self, data):
        if data.shape[0] == 0:
            return

        DataRec = self.DataVer

        # Clear plots for redraw
        self.__graph.clearPlots()

        # Select data slices by angle
        ang0, ang1 = self.__ang_plot.get_region()
        ang_select = ((ang0 <= data[:, DataRec.COL_ANGLE]) & (data[:, DataRec.COL_ANGLE] <= ang1))

        # Select data slices by distance
        px0, px1 = self.__px_plot.get_region()
        px_select = ((px0 <= data[:, DataRec.COL_PX]) & (data[:, DataRec.COL_PX] <= px1))

        # Select data slices by bpm
        bpm0, bpm1 = self.__bpm_plot.get_region()
        bpm_select = ((bpm0 <= data[:, DataRec.COL_BPM]) & (data[:, DataRec.COL_BPM] <= bpm1))

        # Select data slices by rotation
        rot0, rot1 = self.__rot_plot.get_region()
        rot_select = ((rot0 <= data[:, DataRec.COL_ROT]) & (data[:, DataRec.COL_ROT] <= rot1))

        # Draw available rotation points on the plot to the right   
        unique_angs = np.unique(data[:, DataRec.COL_ANGLE])
        self.__ang_plot.plot(unique_angs)

        unique_pxs = np.unique(data[:, DataRec.COL_PX])
        self.__px_plot.plot(unique_pxs)

        unique_bpms = np.unique(data[:, DataRec.COL_BPM])
        self.__bpm_plot.plot(unique_bpms)

        unique_rots = np.unique(data[:, DataRec.COL_ROT])
        self.__rot_plot.plot(unique_rots)

        # Selected rotation region has no data. Nothing else to do
        if not any(ang_select & px_select & bpm_select & rot_select):
            return

        # Determine data selected by BPM
        data_select = ang_select & px_select & bpm_select & rot_select
        if not any(bpm_select):
            # Selected region has no data. Nothing else to do
            return

        # Determine data selected by osu!px
        if self.dev_select == self.DEV_X:
            self.__graph.setTitle('Aim dev-x (bpm)')
            stdevs = data[data_select, DataRec.COL_STDEV_X]
        elif self.dev_select == self.DEV_Y:
            self.__graph.setTitle('Aim dev-y (bpm)')
            stdevs = data[data_select, DataRec.COL_STDEV_Y]
        elif self.dev_select == self.DEV_XY:
            self.__graph.setTitle('Aim dev-xy (bpm)')
            stdevs = (data[data_select, DataRec.COL_STDEV_X]**2 + data[data_select, DataRec.COL_STDEV_Y]**2)**0.5
        elif self.dev_select == self.DEV_T:
            self.__graph.setTitle('Aim dev-t (bpm)')
            stdevs = data[data_select, DataRec.COL_STDEV_T]
        elif self.dev_select == self.AVG_X:
            self.__graph.setTitle('Aim avg-x (bpm)')
            stdevs = data[data_select, DataRec.COL_AVG_X]
        elif self.dev_select == self.AVG_Y:
            self.__graph.setTitle('Aim avg-y (bpm)')
            stdevs = data[data_select, DataRec.COL_AVG_Y]
        elif self.dev_select == self.AVG_T:
            self.__graph.setTitle('Aim avg-t (bpm)')
            stdevs = data[data_select, DataRec.COL_AVG_T]
            
        num_notes = data[data_select, DataRec.COL_NUM]

        if self.avg_data_points:
            # Average all displayed data points
            num_points = len(stdevs)

            # Average overlapping data points (those that fall on same angle)
            stdevs = np.asarray([ np.sort(stdevs[num_notes == num_note])[:num_points].mean() for num_note in np.unique(num_notes) ])
            num_notes = np.unique(num_notes)

            # Get sort mapping to make points on line graph connect in proper order
            idx_sort = np.argsort(num_notes)
            num_notes = num_notes[idx_sort]
            stdevs = stdevs[idx_sort]

        # Draw plot
        color = (  0, 100, 255, 200)
        self.__graph.plot(x=num_notes, y=stdevs, symbol='o', symbolPen=None, symbolSize=5, pen=None, symbolBrush=color)
    

    def __angle_region_event(self):
        # When the selection on angle plot changes, reprocess main graph
        StddevGraphNumNotes.plot_data(self, self.data)


    def __bpm_region_event(self):
        # When the selection on number of notes plot changes, reprocess main graph
        StddevGraphNumNotes.plot_data(self, self.data)


    def __px_region_event(self):
        # When the selection on distance plot changes, reprocess main graph
        StddevGraphNumNotes.plot_data(self, self.data)


    def __rot_region_event(self):
        # When the selection on rotation plot changes, reprocess main graph
        StddevGraphNumNotes.plot_data(self, self.data)


    def set_dev(self, dev):
        self.__dev_marker_95.setPos(dev/4)