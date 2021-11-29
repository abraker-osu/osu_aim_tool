import pyqtgraph
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore

import numpy as np

from app.misc._utils import Utils


class StddevGraphSkill():

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
        self.__graph = pyqtgraph.PlotWidget(title='Aim dev-x (skill)')
        self.__graph.getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.__graph.getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.__graph.enableAutoRange(axis='x', enable=False)
        self.__graph.enableAutoRange(axis='y', enable=False)
        self.__graph.setLimits(xMin=-10, xMax=190, yMin=-10, yMax=1000)
        self.__graph.setRange(xRange=[-10, 190], yRange=[-10, 200])
        self.__graph.setLabel('left', 'slope', units='ms', unitPrefix='')
        self.__graph.setLabel('bottom', 'angle', units='deg', unitPrefix='')
        self.__graph.addLegend()

        self.__layout = QtGui.QHBoxLayout(self.graphs[self.__id]['widget'])
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(2)
        self.__layout.addWidget(self.__graph)


    def plot_data(self, data):
        if data.shape[0] == 0:
            return

        # Clear plots for redraw
        self.__graph.clearPlots()

        # Colored gradient r->g->b multiple plots at different angles
        unique_angs = np.unique(data[:, self.COL_ANGLE])
        if unique_angs.shape[0] == 0:
            # Data selection empty
            return

        slopes = []
        angles = []

        # Adds a plot for every unique BPM recorded
        for angle in unique_angs:
            # Determine data selected by angle
            ang_select = (data[:, self.COL_ANGLE] == angle)
            data_select = ang_select
            if not any(data_select):
                # Selected region has no data. Nothing else to do
                continue

            # Extract relavent data
            if self.dev_select == self.DEV_X:
                self.__graph.setTitle('Aim dev-x (vel)')
                stdevs = data[data_select, self.COL_STDEV_X]
            elif self.dev_select == self.DEV_Y:
                self.__graph.setTitle('Aim dev-y (vel)')
                stdevs = data[data_select, self.COL_STDEV_Y]
            elif self.dev_select == self.DEV_XY:
                self.__graph.setTitle('Aim dev-xy (vel)')
                stdevs = (data[data_select, self.COL_STDEV_X]**2 + data[data_select, self.COL_STDEV_Y]**2)**0.5

            pxs = data[data_select, self.COL_PX]
            bpms = data[data_select, self.COL_BPM]

            # Velocity
            vels = pxs*bpms/60

            # Calc linear regression
            m, b = Utils.linear_regresion(vels, stdevs)
            if type(m) == type(None) or type(b) == type(None):
                continue

            slopes.append(m*2*1000)
            angles.append(angle)

        # Plot slope vs angle
        self.__graph.plot(x=angles, y=slopes, pen='y')