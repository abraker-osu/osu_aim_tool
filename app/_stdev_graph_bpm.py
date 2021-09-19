import pyqtgraph
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore

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
            widget      = pyqtgraph.PlotWidget(title='Aim variance (bpm)'),
        )

        self.graphs[self.__id]['widget'].getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].setLabel('left', 'variance', units='σ²', unitPrefix='')
        self.graphs[self.__id]['widget'].setLabel('bottom', 'bpm', units='bpm', unitPrefix='')
        
        self.graphs[self.__id]['widget'].addLegend()
        self.graphs[self.__id]['widget'].getPlotItem().legend.setBrush(pyqtgraph.mkBrush(53, 54, 70, 150))


    def plot_data(self, data):
        if data.shape[0] == 0:
            return

        unique_pxs = np.unique(data[:, self.COL_PX])

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

        self.graphs[self.__id]['widget'].clearPlots()
        for px in unique_pxs:
            symbol = random.choice([ 't', 'star', 'o', 'd', 'h', 's', 't1', 'p' ])

            px_filter = (data[:, self.COL_PX] == px)
            stddevs = data[px_filter, self.COL_STDEV]
            bpms = data[px_filter, self.COL_BPM]

            idx_sort = np.argsort(bpms)
            color = px_lut.map(px, 'qcolor')

            self.graphs[self.__id]['widget'].plot(x=bpms[idx_sort], y=stddevs[idx_sort]**2, symbol=symbol, symbolPen='w', symbolSize=10, pen=color, symbolBrush=color, name=f'{px} px')