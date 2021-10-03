import pyqtgraph
from pyqtgraph.Qt import QtGui

import numpy as np
import random


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
        self.__graph.setLimits(xMin=0, xMax=1200, yMin=-10, yMax=800)
        self.__graph.setLabel('left', 'deviation', units='σ', unitPrefix='')
        self.__graph.setLabel('bottom', 'bpm', units='60/s', unitPrefix='')
        self.__graph.addLegend()
        self.__graph.getPlotItem().legend.setBrush(pyqtgraph.mkBrush(53, 54, 70, 150))

        # Interactive region item
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

        self.__rot_region = pyqtgraph.LinearRegionItem(values=(0, 10), orientation='horizontal')
        self.__rot_region.setBounds((0, 360))
        self.__rot_region.setSpan(0, 22.5)
        self.__rot_region.sigRegionChanged.connect(lambda: StddevGraphBpm.__rot_region_event(self))

        # Put it all together
        self.__layout = QtGui.QHBoxLayout(self.graphs[self.__id]['widget'])
        self.__layout.addWidget(self.__graph)
        self.__rot_plot.addItem(self.__rot_region)
        self.__layout.addWidget(self.__rot_plot)


    def plot_data(self, data):
        if data.shape[0] == 0:
            return

        unique_pxs = np.unique(data[:, self.COL_PX])
        unique_pxs = unique_pxs[::int(max(1, unique_pxs.shape[0]/5))]  # Limit display to 5 or 6 plots

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

        rot0, rot1 = self.__rot_region.getRegion()
        rot_select = ((rot0 <= data[:, self.COL_ROT]) & (data[:, self.COL_ROT] <= rot1))

        unique_rots = np.unique(data[:, self.COL_ROT])
        self.__rot_plot.clearPlots()
        self.__rot_plot.plot(np.zeros(unique_rots.shape[0]), unique_rots, pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')

        self.__graph.clearPlots()
        for px in unique_pxs:
            symbol = random.choice([ 't', 'star', 'o', 'd', 'h', 's', 't1', 'p' ])

            px_select = (data[:, self.COL_PX] == px)
            stddevs = data[px_select & rot_select, self.COL_STDEV_X]
            bpms = data[px_select & rot_select, self.COL_BPM]

            idx_sort = np.argsort(bpms)
            color = px_lut.map(px, 'qcolor')

            self.__graph.plot(x=bpms[idx_sort], y=stddevs[idx_sort], symbol=symbol, symbolPen='w', symbolSize=10, pen=color, symbolBrush=color, name=f'{px} px')


    def __rot_region_event(self):
        StddevGraphBpm.plot_data(self, self.data)