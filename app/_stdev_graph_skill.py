import pyqtgraph
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore

import math
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

        self.__error_bars = pyqtgraph.ErrorBarItem(beam=0.5)
        self.__graph.addItem(self.__error_bars)

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

        unique_angs = np.sort(unique_angs)
        plot_data = np.zeros((unique_angs.shape[0], 3))

        # Adds a plot for every unique BPM recorded
        for angle, i in zip(unique_angs, range(data.shape[0])):
            # Determine data selected by angle
            ang_select = (data[:, self.COL_ANGLE] == angle)
            data_select = ang_select
            if not any(data_select):
                # Selected region has no data. Nothing else to do
                plot_data[i, 0] = np.nan
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
                plot_data[i, 0] = np.nan
                continue

            # Record slope and angle
            plot_data[i, 0] = angle
            plot_data[i, 1] = m*2*1000

            if stdevs.shape[0] < 2:
                plot_data[i, 2] = np.nan
                continue

            # Calc and record standard error
            y_model = m*vels + b                # model: y = mx + b
            x_model = (stdevs - b)/m            # model: x = (y - b)/m

            m_dev_y = np.std(stdevs - y_model)  # deviation of y from model
            m_dev_x = np.std(vels - x_model)    # deviation of x from model

            if m_dev_x == 0:
                plot_data[i, 2] = np.nan
                continue

            # Standard error of slope @ 95% confidence interval
            m_se_95 = (m_dev_y/m_dev_x)/math.sqrt(stdevs.shape[0] - 2)*1.96
            plot_data[i, 2] = m_se_95*2*1000

        # Plot slope vs angle
        plot_data = plot_data[~np.isnan(plot_data[:, 0])]  # Remove nan
        self.__graph.plot(x=plot_data[:, 0], y=plot_data[:, 1], pen='y')

        # Plot error bars
        plot_data = plot_data[~np.isnan(plot_data[:, 2])]  # Remove nan
        self.__error_bars.setData(x=plot_data[:, 0], y=plot_data[:, 1], top=plot_data[:, 2], bottom=plot_data[:, 2]) 