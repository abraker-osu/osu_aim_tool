import pyqtgraph
from pyqtgraph.Qt import QtGui

import numpy as np


class StddevGraphVel():

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
        self.__graph = pyqtgraph.PlotWidget(title='Aim dev-x (vel)')
        self.__graph.getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.__graph.getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.__graph.setLimits(xMin=0, xMax=5000, yMin=-10, yMax=75)
        self.__graph.setLabel('left', 'deviation', units='σ', unitPrefix='')
        self.__graph.setLabel('bottom', 'velocity', units='osu!px/s', unitPrefix='')
        self.__graph.addLegend()

        # Used to set text in legend item
        self.__label_style = pyqtgraph.PlotDataItem(pen=(0,0,0))
        self.__graph.getPlotItem().legend.addItem(self.__label_style, '')
        self.__text = self.__graph.getPlotItem().legend.getLabel(self.__label_style)
        
        # Interactive region plot to the right
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
        self.__rot_region.sigRegionChanged.connect(lambda: StddevGraphVel.__rot_region_event(self))

        # Put it all together
        self.__layout = QtGui.QHBoxLayout(self.graphs[self.__id]['widget'])
        self.__layout.addWidget(self.__graph)
        self.__rot_plot.addItem(self.__rot_region)
        self.__layout.addWidget(self.__rot_plot)


    def plot_data(self, data):
        if data.shape[0] == 0:
            return

        # Select data slices by rotation
        rot0, rot1 = self.__rot_region.getRegion()
        rot_select = ((rot0 <= data[:, self.COL_ROT]) & (data[:, self.COL_ROT] <= rot1))

        unique_rots = np.unique(data[:, self.COL_ROT])
        self.__rot_plot.clearPlots()
        self.__rot_plot.plot(np.zeros(unique_rots.shape[0]), unique_rots, pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')

        # Extract relavent data
        stdevs = data[rot_select, self.COL_STDEV_X]
        pxs = data[rot_select, self.COL_PX]
        bpms = data[rot_select, self.COL_BPM]

        # Velocity
        vel = pxs*bpms/60
        
        # Clear plots for redraw
        self.__graph.clearPlots()

        # Draw data plot
        self.__graph.plot(x=vel, y=stdevs, pen=None, symbol='o', symbolPen=None, symbolSize=10, symbolBrush=(100, 100, 255, 200))
        
        # Model processing. Needs at least 2 points.
        filter_0 = vel != 0  # Filter out zeros in vel
        if vel[filter_0].shape[0] >= 2:
            m = np.mean(stdevs[filter_0]/vel[filter_0])
            
            # Draw model plot
            self.__graph.plot(x=[0, max(vel)], y=[0, m*max(vel)], pen=(100, 100, 0, 150))

            # Calc and display R^2 
            corr_mat = np.corrcoef(vel, stdevs)
            corr_xy = corr_mat[0, 1]
            r_sq = corr_xy**2

            self.__text.setText(f'R^2 = {r_sq:.2f}')
        else:
            self.__text.setText(f'')


    def __rot_region_event(self):
        StddevGraphVel.plot_data(self, self.data)