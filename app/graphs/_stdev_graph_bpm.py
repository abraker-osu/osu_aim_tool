import pyqtgraph
from pyqtgraph.Qt import QtGui

import math
import numpy as np
import random

from app.misc._utils import MathUtils
from app.misc._select_plot import SelectPlot


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
        self.__graph.enableAutoRange(axis='x', enable=False)
        self.__graph.enableAutoRange(axis='y', enable=False)
        self.__graph.setLimits(xMin=0, xMax=1200, yMin=-100, yMax=200)
        self.__graph.setRange(xRange=[-10, 500], yRange=[-10, 20])
        self.__graph.setLabel('left', 'deviation', units='σ', unitPrefix='')
        self.__graph.setLabel('bottom', 'bpm', units='1/(60*s)', unitPrefix='')
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
            region_event = lambda: StddevGraphBpm.__region_event(self)
        )

        # Interactive region plot to the right to select distance between notes in data
        self.__px_plot = SelectPlot(
            view_min = 0,  view_max = 512,
            val_min  = 0,  val_max  = 512,
            init_min = 75, init_max = 125,
            label = 'Dist',
            region_event = lambda: StddevGraphBpm.__region_event(self),
            mouse_ctrl = True
        )

        # Interactive region plot to the right to select angle of rotation in data
        self.__rot_plot = SelectPlot(
            view_min = 0,  view_max = 180,
            val_min  = 0,  val_max  = 180,
            init_min = 0,  init_max = 30,
            label = 'Rot',
            region_event = lambda: StddevGraphBpm.__region_event(self)
        )

        # Interactive region plot to the right to select number of notes in data
        self.__num_plot = SelectPlot(
            view_min = 0,  view_max = 2000,
            val_min  = 0,  val_max  = 2000,
            init_min = 0,  init_max = 120,
            label = '# Notes',
            region_event = lambda: StddevGraphBpm.__region_event(self),
            mouse_ctrl = True
        )

        # Put it all together
        self.__layout = QtGui.QHBoxLayout(self.graphs[self.__id]['widget'])
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(2)
        self.__layout.addWidget(self.__graph)
        self.__layout.addWidget(self.__ang_plot)
        self.__layout.addWidget(self.__px_plot)
        self.__layout.addWidget(self.__rot_plot)
        self.__layout.addWidget(self.__num_plot)


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

        # Select data slices by rotation
        rot0, rot1 = self.__rot_plot.get_region()
        rot_select = ((rot0 <= data[:, DataRec.COL_ROT]) & (data[:, DataRec.COL_ROT] <= rot1))

        # Select data slices by number of notes
        num0, num1 = self.__num_plot.get_region()
        num_select = ((num0 <= data[:, DataRec.COL_NUM]) & (data[:, DataRec.COL_NUM] <= num1))

        # Draw available rotation points on the plot to the right   
        unique_angs = np.unique(data[:, DataRec.COL_ANGLE])
        self.__ang_plot.plot(unique_angs)

        unique_pxs = np.unique(data[:, DataRec.COL_PX])
        self.__px_plot.plot(unique_pxs)

        unique_rots = np.unique(data[:, DataRec.COL_ROT])
        self.__rot_plot.plot(unique_rots)

        unique_nums = np.unique(data[:, DataRec.COL_NUM])
        self.__num_plot.plot(unique_nums)

        # Selected rotation region has no data. Nothing else to do
        if not any(ang_select & px_select & rot_select & num_select):
            return

        # Colored gradient r->g->b multiple plots at different osu!px
        unique_pxs = np.unique(data[rot_select & px_select & ang_select & num_select, DataRec.COL_PX])

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
            px_select = (data[:, DataRec.COL_PX] == px)
            data_select = px_select & ang_select & rot_select & num_select
            if not any(px_select):
                # Selected region has no data. Nothing else to do
                continue

            bpms = data[data_select, DataRec.COL_BPM]

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
            
            if self.avg_data_points:
                # Use best N points for data display
                num_points = min(len(stdevs), self.MAX_NUM_DATA_POINTS)

                # Average overlapping data points (those that fall on same bpm)
                stdevs = np.asarray([ np.sort(stdevs[bpms == bpm])[:num_points].mean() for bpm in np.unique(bpms) ])
                bpms = np.unique(bpms)

                # Get sort mapping to make points on line graph connect in proper order
                idx_sort = np.argsort(bpms)
                bpms = bpms[idx_sort]
                stdevs = stdevs[idx_sort]

            # Draw plot
            color = px_lut.map(px, 'qcolor')
            
            m, b = MathUtils.linear_regresion(bpms, stdevs)
            if type(m) == type(None) or type(b) == type(None):
                # Linear regression failed, just plot the points
                self.__graph.plot(x=bpms, y=stdevs, symbol='o', symbolPen=None, symbolSize=5, pen=None, symbolBrush=color, name=f'{px} osu!px')
                continue

            if self.model_compensation:
                y_model = m*bpms + b
                self.__graph.plot(x=bpms, y=stdevs - y_model, symbol='o', symbolPen=None, symbolSize=5, pen=None, symbolBrush=color, name=f'{px} osu!px   σ = {np.std(stdevs - y_model):.2f}  m={m:.5f}  b={b:.2f}')
            else:
                self.__graph.plot(x=bpms, y=stdevs, symbol='o', symbolPen=None, symbolSize=5, pen=None, symbolBrush=color, name=f'{px} osu!px')

    
    def __region_event(self):
        # When the selection plot changes, reprocess main graph
        StddevGraphBpm.plot_data(self, self.data)


    def set_dev(self, dev):
        self.__dev_marker_95.setPos(dev/4)
