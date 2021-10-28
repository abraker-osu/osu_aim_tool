import pyqtgraph
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore

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
        self.__graph.setLimits(xMin=0, xMax=5000, yMin=-10, yMax=200)
        self.__graph.setLabel('left', 'deviation', units='σ', unitPrefix='')
        self.__graph.setLabel('bottom', 'velocity', units='osu!px/s', unitPrefix='')
        self.__graph.addLegend()

        # Deviation marker indicating expected deviation according to set CS
        self.__dev_marker = pyqtgraph.InfiniteLine(angle=0, movable=False, pen=pyqtgraph.mkPen(color=(200, 200, 0, 100), style=pyqtgraph.QtCore.Qt.DashLine))
        self.__graph.addItem(self.__dev_marker, ignoreBounds=True)

        # Used to set text in legend item
        self.__label_style = pyqtgraph.PlotDataItem(pen=(0,0,0))
        self.__graph.getPlotItem().legend.addItem(self.__label_style, '')
        self.__text = self.__graph.getPlotItem().legend.getLabel(self.__label_style)
        
        # Interactive region plot to the right to select angle of rotation in data
        self.__rot_plot = pyqtgraph.PlotWidget()
        self.__rot_plot.setXRange(-0.5, 0.5)
        self.__rot_plot.setYRange(0, 180)
        self.__rot_plot.getViewBox().setMouseEnabled(x=False, y=False)
        self.__rot_plot.enableAutoRange(axis='x', enable=False)
        self.__rot_plot.enableAutoRange(axis='y', enable=False)
        self.__rot_plot.hideAxis('bottom')
        self.__rot_plot.hideAxis('left')
        self.__rot_plot.showAxis('right')
        self.__rot_plot.setFixedWidth(64)

        # Slider region allowing to select angle of rotation
        self.__rot_region = pyqtgraph.LinearRegionItem(values=(0, 10), orientation='horizontal')
        self.__rot_region.setBounds((0, 180))
        self.__rot_region.setRegion((0, 30))
        self.__rot_region.sigRegionChanged.connect(lambda: StddevGraphVel.__rot_region_event(self))

        # Label for the interactive region plot
        self.__rot_label = QtGui.QLabel('    Rot')
        self.__rot_label.setStyleSheet('background-color: black')

        # Interactive region plot to the right to select angle between notes in data
        self.__ang_plot = pyqtgraph.PlotWidget()
        self.__ang_plot.setXRange(-0.5, 0.5)
        self.__ang_plot.setYRange(0, 180)
        self.__ang_plot.getViewBox().setMouseEnabled(x=False, y=False)
        self.__ang_plot.enableAutoRange(axis='x', enable=False)
        self.__ang_plot.enableAutoRange(axis='y', enable=False)
        self.__ang_plot.hideAxis('bottom')
        self.__ang_plot.hideAxis('left')
        self.__ang_plot.showAxis('right')
        self.__ang_plot.setFixedWidth(64)

        # Slider region allowing to select angle between notes
        self.__ang_region = pyqtgraph.LinearRegionItem(values=(0, 10), orientation='horizontal')
        self.__ang_region.setBounds((0, 180))
        self.__ang_region.setRegion((0, 30))
        self.__ang_region.sigRegionChanged.connect(lambda: StddevGraphVel.__angle_region_event(self))

        # Label for the interactive region plot
        self.__ang_label = QtGui.QLabel('    Angle')
        self.__ang_label.setStyleSheet('background-color: black')

        # Put it all together
        self.__rot_plot.addItem(self.__rot_region)
        self.__ang_plot.addItem(self.__ang_region)
        
        self.__rot_layout = QtGui.QVBoxLayout()
        self.__rot_layout.setSpacing(0)
        self.__rot_layout.addWidget(self.__rot_plot)
        self.__rot_layout.addWidget(self.__rot_label)

        self.__ang_layout = QtGui.QVBoxLayout()
        self.__ang_layout.setSpacing(0)
        self.__ang_layout.addWidget(self.__ang_plot)
        self.__ang_layout.addWidget(self.__ang_label)

        self.__layout = QtGui.QHBoxLayout(self.graphs[self.__id]['widget'])
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(2)
        self.__layout.addWidget(self.__graph)
        self.__layout.addLayout(self.__rot_layout)
        self.__layout.addLayout(self.__ang_layout)


    def plot_data(self, data):
        if data.shape[0] == 0:
            return

        # Clear plots for redraw
        self.__graph.clearPlots()

        # Select data slices by rotation
        rot0, rot1 = self.__rot_region.getRegion()
        rot_select = ((rot0 <= data[:, self.COL_ROT]) & (data[:, self.COL_ROT] <= rot1))

        # Select data slices by angle
        ang0, ang1 = self.__ang_region.getRegion()
        ang_select = ((ang0 <= data[:, self.COL_ANGLE]) & (data[:, self.COL_ANGLE] <= ang1))

        unique_rots = np.unique(data[:, self.COL_ROT])
        self.__rot_plot.clearPlots()
        self.__rot_plot.plot(np.zeros(unique_rots.shape[0]), unique_rots, pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')

        unique_angs = np.unique(data[:, self.COL_ANGLE])
        self.__ang_plot.clearPlots()
        self.__ang_plot.plot(np.zeros(unique_angs.shape[0]), unique_angs, pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')

        # Selected rotation region has no data. Nothing else to do
        data_select = rot_select & ang_select
        if not any(data_select):
            return

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
        vel = pxs*bpms/60

        # Draw data plot
        self.__graph.plot(x=vel, y=stdevs, pen=None, symbol='o', symbolPen=None, symbolSize=10, symbolBrush=(100, 100, 255, 200))
        
        # Model processing. Needs at least 2 points.
        if vel.shape[0] >= 2:
            # Model linear curve
            # Visual example of how this works: https://i.imgur.com/k7H8bLe.png
            # 1) Take points on y-axis and x-axis, and split them into half - resulting in two groups
            median_x = np.mean(stdevs)
            median_y = np.mean(vel)

            g1 = (stdevs < median_x) & (vel < median_y)    # Group 1 select
            g2 = (stdevs >= median_x) & (vel >= median_y)  # Group 2 select
            
            # 2) Take the center of gravity for each of the two groups
            #    Those become points p1 and p2 to fit a line through
            p1x = np.mean(vel[g1])
            p1y = np.mean(stdevs[g1])

            p2x = np.mean(vel[g2])
            p2y = np.mean(stdevs[g2])

            # 3) Calculate slope and y-intercept
            m = (p1y - p2y)/(p1x - p2x)
            b = p1y - m*p1x
            
            # Draw model plot
            self.__graph.plot(x=[0, max(vel)], y=[b, m*max(vel) + b], pen=(100, 100, 0, 150))

            # Calc and display R^2 
            corr_mat = np.corrcoef(vel, stdevs)
            corr_xy = corr_mat[0, 1]
            r_sq = corr_xy**2

            self.__text.setText(f'R^2 = {r_sq:.2f}  m={m:.3f}  b={b:.2f}')
        else:
            self.__text.setText(f'')

        if self.model_compensation:
            self.__graph.clearPlots()

            y_model = m*vel + b

            self.__text.setText(f'σ = {np.std(stdevs - y_model):.2f}  m={m:.3f}  b={b:.2f}')
            self.__graph.plot(x=vel, y=stdevs - y_model, pen=None, symbol='o', symbolPen=None, symbolSize=10, symbolBrush=(100, 100, 255, 200))
            self.__graph.plot(x=[0, max(vel)], y=[0, 0], pen=(100, 100, 0, 150))



    def __rot_region_event(self):
        # When the selection on rotation plot changes, reprocess main graph
        StddevGraphVel.plot_data(self, self.data)

    
    def __angle_region_event(self):
        # When the selection on angle plot changes, reprocess main graph
        StddevGraphVel.plot_data(self, self.data)


    def set_dev(self, dev):
        self.__dev_marker.setPos(dev)