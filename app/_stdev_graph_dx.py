import pyqtgraph
from pyqtgraph.Qt import QtGui

import numpy as np
import random


class StddevGraphDx():

    def __init__(self, pos, relative_to=None, dock_name=''):
        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            dock_name   = dock_name,
            widget      = QtGui.QWidget(),
        )

        self.__graph = pyqtgraph.PlotWidget(title='Aim var-x (px)')
        self.__graph.getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.__graph.getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.__graph.setLimits(xMin=0, xMax=600, yMin=-10, yMax=800)
        self.__graph.setLabel('left', 'variance', units='σ²', unitPrefix='')
        self.__graph.setLabel('bottom', 'distance', units='osu!px', unitPrefix='')
        self.__graph.addLegend()
        self.__graph.getPlotItem().legend.setBrush(pyqtgraph.mkBrush(53, 54, 70, 150))
        
        # Interactive region plot to the right to select angle of rotation in data
        self.__rot_plot = pyqtgraph.PlotWidget()
        self.__rot_plot.setXRange(-0.5, 0.5)
        self.__rot_plot.setYRange(0, 360)
        self.__rot_plot.getViewBox().setMouseEnabled(x=False, y=False)
        self.__rot_plot.enableAutoRange(axis='x', enable=False)
        self.__rot_plot.enableAutoRange(axis='y', enable=False)
        self.__rot_plot.hideAxis('bottom')
        self.__rot_plot.hideAxis('left')
        self.__rot_plot.showAxis('right')
        self.__rot_plot.setFixedWidth(64)

        # Slider region allowing to select angle of rotation
        self.__rot_region = pyqtgraph.LinearRegionItem(values=(0, 10), orientation='horizontal')
        self.__rot_region.setBounds((0, 360))
        self.__rot_region.setSpan(0, 22.5)
        self.__rot_region.sigRegionChanged.connect(lambda: StddevGraphDx.__rot_region_event(self))

        # Label for the interactive region plot
        self.__rot_label = QtGui.QLabel('    Rot')
        self.__rot_label.setStyleSheet('background-color: black')

        # Put it all together
        self.__rot_plot.addItem(self.__rot_region)
        
        self.__rot_layout = QtGui.QVBoxLayout()
        self.__rot_layout.setSpacing(0)
        self.__rot_layout.addWidget(self.__rot_plot)
        self.__rot_layout.addWidget(self.__rot_label)

        self.__layout = QtGui.QHBoxLayout(self.graphs[self.__id]['widget'])
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(2)
        self.__layout.addWidget(self.__graph)
        self.__layout.addLayout(self.__rot_layout)


    def plot_data(self, data):
        if data.shape[0] == 0:
            return

        self.__graph.clearPlots()

        # Colored gradient r->g->b multiple plots at different osu!px
        unique_bpms = np.unique(data[:, self.COL_BPM])
        unique_bpms = unique_bpms[::int(max(1, unique_bpms.shape[0]/5))]  # Limit display to 5 or 6 plots

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

        # Determine data selected by angle of rotation
        rot0, rot1 = self.__rot_region.getRegion()
        rot_select = ((rot0 <= data[:, self.COL_ROT]) & (data[:, self.COL_ROT] <= rot1))

        # Selected rotation region has no data. Nothing else to do
        if not any(rot_select):
            return

        # Draw available rotation points on the plot to the right
        unique_rots = np.unique(data[:, self.COL_ROT])
        self.__rot_plot.clearPlots()
        self.__rot_plot.plot(np.zeros(unique_rots.shape[0]), unique_rots, pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')

        # Main plot - deviation vs osu!px
        # Adds a plot for every unique BPM recorded
        for bpm in unique_bpms:
            # Determine data selected by BPM
            bpm_select = (data[:, self.COL_BPM] == bpm)
            if not any(bpm_select):
                continue

            # Determine data selected by osu!px
            stddevs = data[bpm_select & rot_select, self.COL_STDEV_X]
            pxs = data[bpm_select & rot_select, self.COL_PX]

            # Get sort mapping to make points on line graph connect in proper order
            idx_sort = np.argsort(pxs)

            # Draw plot
            symbol = random.choice([ 't', 'star', 'o', 'd', 'h', 's', 't1', 'p' ])
            color = bpm_lut.map(bpm, 'qcolor')
            self.__graph.plot(x=pxs[idx_sort], y=stddevs[idx_sort]**2, symbol=symbol, symbolPen='w', symbolSize=10, pen=color, symbolBrush=color, name=f'{bpm} bpm')


    def __rot_region_event(self):
        StddevGraphDx.plot_data(self, self.data)