import pyqtgraph
import numpy as np
from pyqtgraph import QtCore, QtGui


class TimingPlot(pyqtgraph.GraphItem):

    def __init__(self, color=(255, 255, 255, 255), width=3):
        pyqtgraph.GraphItem.__init__(self)
        pyqtgraph.setConfigOptions(antialias=True)

        self.pen = pyqtgraph.mkPen(width=width, color=color)
        self.pen.setCapStyle(QtCore.Qt.RoundCap)
        self.setPen(self.pen)
    

    def setTimings(self, start_times=[], end_times=[], y_pos=0, color=(255, 255, 255, 255), width=3):
        try:
            if len(start_times) == 0 or len(end_times) == 0:
                self.scatter.clear()
                self.pos = None
                return
        except ValueError: 
            return

        if len(start_times) != len(end_times):
            print(f'Warning: start_times and end_times are NOT the same length: {len(start_times)} != {len(end_times)}')
            return

        self.pen = pyqtgraph.mkPen(width=width, color=color)
        self.setPen(self.pen)

        num_intervals = len(start_times)

        pos  = np.zeros((num_intervals*2, 2), dtype=np.float)
        adj  = np.zeros((num_intervals, 2), dtype=np.int)
        size = np.zeros(num_intervals*2, dtype=np.int)

        pos[::2, 0] = start_times
        pos[1::2, 0] = end_times
        pos[:, 1] = y_pos

        adj[:, 0] = np.arange(start=0, stop=num_intervals*2, step=2)
        adj[:, 1] = np.arange(start=0, stop=num_intervals*2, step=2) + 1

        self.setData(pos=pos, adj=adj, size=size, pxMode=True)
