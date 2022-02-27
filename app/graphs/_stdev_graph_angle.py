import pyqtgraph
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore

import math
import random
import numpy as np

from app.misc._utils import MathUtils
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

        DataRec = self.DataVer

        # Clear plots for redraw
        self.__graph.clearPlots()

        # Select data slices by bpm
        bpm0, bpm1 = self.__bpm_plot.get_region()
        bpm_select = ((bpm0 <= data[:, DataRec.COL_BPM]) & (data[:, DataRec.COL_BPM] <= bpm1))

        # Select data slices by distance
        px0, px1 = self.__px_plot.get_region()
        px_select = ((px0 <= data[:, DataRec.COL_PX]) & (data[:, DataRec.COL_PX] <= px1))

        # Select data slices by rotation
        rot0, rot1 = self.__rot_plot.get_region()
        rot_select = ((rot0 <= data[:, DataRec.COL_ROT]) & (data[:, DataRec.COL_ROT] <= rot1))

        unique_bpms = np.unique(data[:, DataRec.COL_BPM])
        self.__bpm_plot.plot(unique_bpms)

        unique_pxs = np.unique(data[:, DataRec.COL_PX])
        self.__px_plot.plot(unique_pxs)

        unique_rots = np.unique(data[:, DataRec.COL_ROT])
        self.__rot_plot.plot(unique_rots)

        # Selected rotation region has no data. Nothing else to do
        if not any(bpm_select & px_select & rot_select):
            return

        # Colored gradient r->g->b multiple plots at different osu!px
        unique_bpms = np.unique(data[bpm_select & px_select & rot_select, DataRec.COL_BPM])

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
            data_select = bpm_select & px_select & rot_select
            if not any(data_select):
                # Selected region has no data. Nothing else to do
                continue

            angles = data[data_select, DataRec.COL_ANGLE]

            # Determine data selected by osu!px
            if self.dev_select == self.DEV_X:
                self.__graph.setTitle('Aim dev-x (angle)')
                stdevs = data[data_select, DataRec.COL_STDEV_X]
            elif self.dev_select == self.DEV_Y:
                self.__graph.setTitle('Aim dev-y (angle)')
                stdevs = data[data_select, DataRec.COL_STDEV_Y]
            elif self.dev_select == self.DEV_XY:
                self.__graph.setTitle('Aim dev-xy (angle)')
                stdevs = (data[data_select, DataRec.COL_STDEV_X]**2 + data[data_select, DataRec.COL_STDEV_Y]**2)**0.5
            elif self.dev_select == self.DEV_T:
                self.__graph.setTitle('Aim dev-t (angle)')
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

                # Average overlapping data points (those that fall on same angle)
                stdevs = np.asarray([ np.sort(stdevs[angles == angle])[:num_points].mean() for angle in np.unique(angles) ])
                angles = np.unique(angles)

                # Get sort mapping to make points on line graph connect in proper order
                idx_sort = np.argsort(angles)
                angles = angles[idx_sort]
                stdevs = stdevs[idx_sort]

            # Draw plot
            color = bpm_lut.map(bpm, 'qcolor')

            if self.dev_select not in [ self.DEV_X, self.DEV_Y, self.DEV_XY ]:
                self.__graph.plot(x=angles, y=stdevs, symbol='o', symbolPen=None, symbolSize=5, pen=None, symbolBrush=color, name=f'{bpm} bpm')
                continue


            if self.dev_select in [ self.DEV_X, self.DEV_Y, self.DEV_XY ]:
                a, b, c = MathUtils.exp_regresion(angles, stdevs)
                if None in (a, b, c):
                    self.__graph.plot(x=angles, y=stdevs, symbol='o', symbolPen=None, symbolSize=5, pen=None, symbolBrush=color, name=f'{bpm} bpm')
                    continue

                y_model = a + b*np.exp(c*angles)
                y_ground = stdevs - y_model

                r_sq = MathUtils.r_squared(stdevs, y_model)
                snr = (np.var(stdevs, ddof=1) / np.mean(np.var(np.lib.stride_tricks.sliding_window_view(stdevs, 5), ddof=1, axis=1)))
                
                x_model = np.linspace(min(angles), max(angles), 100)
                y_model = a + b*np.exp(c*x_model)
                
                label = f'{bpm} bpm  r² = {r_sq:.4f}  snr={snr:.4f}  a={a:.2f}  b={b:.2f}  c={c:.5f}'
                print(f'angle fit (y = a + be^(cx)): {label}')
            

            '''
            if self.dev_select in [ self.DEV_X, self.DEV_Y, self.DEV_XY ]:
                b, c = MathUtils.linear_regresion(angles, stdevs)
                if None in (b, c):
                    self.__graph.plot(x=angles, y=stdevs, symbol='o', symbolPen=None, symbolSize=5, pen=None, symbolBrush=color, name=f'{bpm} bpm')
                    continue

                y_model = b*angles + c
                y_ground = stdevs - y_model

                r_sq = MathUtils.r_squared(stdevs, y_model)
                snr = np.std(stdevs) / np.std(stdevs - y_model)

                x_model = np.linspace(min(angles), max(angles), 100)
                y_model = b*x_model + c
                
                label = f'{bpm} bpm  r² = {r_sq:.4f}  snr={snr:.4f}  b={b:.4f}  c={c:.5f}'
                print(f'angle fit (y = bx + c): {label}')
            ''' 

            if self.model_compensation:
                self.__graph.plot(x=angles, y=y_ground, symbol='o', symbolPen=None, symbolSize=5, pen=None, symbolBrush=color, name=label)
                self.__graph.plot(x=[0, max(angles)], y=[0, 0], pen=(100, 100, 0, 150))
            else:
                self.__graph.plot(x=angles, y=stdevs, symbol='o', symbolPen=None, symbolSize=5, pen=None, symbolBrush=color, name=label)
                self.__graph.plot(x=x_model, y=y_model, pen=(100, 100, 0, 150))  


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
