import pyqtgraph

import numpy as np
import random


class StddevGraphRot():

    def __init__(self, pos, relative_to=None, dock_name=''):
        

        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            dock_name   = dock_name,
            widget      = pyqtgraph.PlotWidget(title='Aim variance (rot)'),
        )

        self.graphs[self.__id]['widget'].getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].setLabel('left', 'variance', units='σ²', unitPrefix='')
        self.graphs[self.__id]['widget'].setLabel('bottom', 'rotation', units='degrees', unitPrefix='')
        
        self.graphs[self.__id]['widget'].addLegend()
        self.graphs[self.__id]['widget'].getPlotItem().legend.setBrush(pyqtgraph.mkBrush(53, 54, 70, 150))


    def plot_data(self, data):
        if data.shape[0] == 0:
            return

        unique_bpms = np.unique(data[:, self.COL_BPM])

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

        self.graphs[self.__id]['widget'].clearPlots()
        for bpm in unique_bpms:
            symbol = random.choice([ 't', 'star', 'o', 'd', 'h', 's', 't1', 'p' ])

            bpm_filter = (data[:, self.COL_BPM] == bpm)
            stddevs = data[bpm_filter, self.COL_STDEV]
            rots = data[bpm_filter, self.COL_ROT]

            idx_sort = np.argsort(rots)

            color = bpm_lut.map(bpm, 'qcolor')
            self.graphs[self.__id]['widget'].plot(x=rots[idx_sort], y=stddevs[idx_sort]**2, symbol=symbol, symbolPen='w', symbolSize=10, pen=color, symbolBrush=color, name=f'{bpm} bpm')
