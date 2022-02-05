import pyqtgraph
from pyqtgraph.Qt import QtGui

import math
import numpy as np
import random

from app.misc._utils import MathUtils
from app.misc._select_plot import SelectPlot



class StddevGraphTapDev():

    def __init__(self, pos, relative_to=None, dock_name=''):
        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            dock_name   = dock_name,
            widget      = QtGui.QWidget(),
        )

        self.__graph = pyqtgraph.PlotWidget(title='Tap dev (ms) vs Aim avg-x (px)')
        self.__graph.getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.__graph.getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.__graph.enableAutoRange(axis='x', enable=False)
        self.__graph.enableAutoRange(axis='y', enable=False)
        self.__graph.setLimits(xMin=-1, xMax=100, yMin=-10, yMax=200)
        self.__graph.setRange(xRange=[-1, 100], yRange=[-10, 20])
        self.__graph.setLabel('left', 'aim average x-pos', units='osu!px', unitPrefix='')
        self.__graph.setLabel('bottom', 'tap deviation', units='ms', unitPrefix='')
        self.__graph.addLegend()
        self.__graph.getPlotItem().legend.setBrush(pyqtgraph.mkBrush(53, 54, 70, 150))

        # Text
        self.__graph_text = pyqtgraph.TextItem('', anchor=(0, 0), )
        self.__graph.addItem(self.__graph_text)
        
        # Interactive region plot to the right to select angle between notes in data
        self.__ang_plot = SelectPlot(
            view_min = 0, view_max = 180,
            val_min  = 0, val_max  = 180,
            init_min = 0, init_max = 180,
            label = 'Angle',
            region_event = lambda: StddevGraphTapDev.__region_event(self)
        )

        # Interactive region plot to the right to select bpm of notes in data
        self.__bpm_plot = SelectPlot(
            view_min = 0,   view_max = 500,
            val_min  = 0,   val_max  = 1200,
            init_min = 170, init_max = 190,
            label = 'BPM',
            region_event = lambda: StddevGraphTapDev.__region_event(self),
            mouse_ctrl = True
        )

        # Interactive region plot to the right to select distance between notes in data
        self.__px_plot = SelectPlot(
            view_min = 0,  view_max = 512,
            val_min  = 0,  val_max  = 512,
            init_min = 75, init_max = 125,
            label = 'Dist',
            region_event = lambda: StddevGraphTapDev.__region_event(self),
            mouse_ctrl = True
        )

        # Put it all together
        self.__layout = QtGui.QHBoxLayout(self.graphs[self.__id]['widget'])
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(2)
        self.__layout.addWidget(self.__graph)
        self.__layout.addWidget(self.__ang_plot)
        self.__layout.addWidget(self.__bpm_plot)
        self.__layout.addWidget(self.__px_plot)

        # Connect signals
        self.__graph.sigRangeChanged.connect(lambda _: StddevGraphTapDev.__on_view_range_changed(self))
        StddevGraphTapDev.__on_view_range_changed(self)


    def plot_data(self, data):
        if data.shape[0] == 0:
            return

        if self.DataVer == self.DataV1:
            self.__graph_text.setText('Unable to display data for v1 data')
            self.__graph.clearPlots()
            return
        else:
            self.__graph_text.setText('')

        DataRec = self.DataVer

        # Clear plots for redraw
        self.__graph.clearPlots()

        # Select data slices by angle
        ang0, ang1 = self.__ang_plot.get_region()
        ang_select = ((ang0 <= data[:, DataRec.COL_ANGLE]) & (data[:, DataRec.COL_ANGLE] <= ang1))

        # Select data slices by bpm
        bpm0, bpm1 = self.__bpm_plot.get_region()
        bpm_select = ((bpm0 <= data[:, DataRec.COL_BPM]) & (data[:, DataRec.COL_BPM] <= bpm1))

        # Select data slices by distance
        px0, px1 = self.__px_plot.get_region()
        px_select = ((px0 <= data[:, DataRec.COL_PX]) & (data[:, DataRec.COL_PX] <= px1))

        # Draw available rotation points on the plot to the right
        unique_angs = np.unique(data[:, DataRec.COL_ANGLE])
        self.__ang_plot.plot(unique_angs)

        unique_bpms = np.unique(data[:, DataRec.COL_BPM])
        self.__bpm_plot.plot(unique_bpms)

        unique_pxs = np.unique(data[:, DataRec.COL_PX])
        self.__px_plot.plot(unique_pxs)
    
        # Selected rotation region has no data. Nothing else to do
        if not any(ang_select & bpm_select & px_select):
            return

        # Colored gradient r->g->b multiple plots at different osu!px
        unique_bpms = np.unique(data[ang_select & bpm_select & px_select, DataRec.COL_BPM])

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
            bpm_select = (data[:, DataRec.COL_BPM] == bpm)
            data_select = bpm_select & px_select & ang_select
            if not any(data_select):
                # Selected region has no data. Nothing else to do
                continue

            # Determine data selected by osu!px
            data_y = data[data_select, DataRec.COL_AVG_X]
            data_x = data[data_select, DataRec.COL_STDEV_T]
                
            if self.avg_data_points:
                # Use best N points for data display
                num_points = min(len(data_y), self.MAX_NUM_DATA_POINTS)

                # Average overlapping data points (those that fall on same px)
                data_y = np.asarray([ np.sort(data_y[data_x == x])[:num_points].mean() for x in np.unique(data_x) ])
                data_x = np.unique(data_x)
            
                # Get sort mapping to make points on line graph connect in proper order
                idx_sort = np.argsort(data_x)
                data_x = data_x[idx_sort]
                data_y = data_y[idx_sort]

            # Draw plot
            color = bpm_lut.map(bpm, 'qcolor')
            self.__graph.plot(x=data_x, y=data_y, symbol='o', symbolPen=None, symbolSize=5, pen=None, symbolBrush=color, name=f'{bpm} bpm')

    
    def __region_event(self):
        # When the selection plot changes, reprocess main graph
        StddevGraphTapDev.plot_data(self, self.data)


    def __on_view_range_changed(self, _=None):
        view = self.__graph.viewRect()
        pos_x = view.left()
        pos_y = view.bottom()

        margin_x = 0.4*(view.right() - view.left())
        margin_y = 0.5*(view.top() - view.bottom())

        self.__graph_text.setPos(pos_x + margin_x, pos_y + margin_y)
