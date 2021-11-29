import pyqtgraph
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore

import numpy as np

from app.misc._utils import Utils


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
        self.__graph.enableAutoRange(axis='x', enable=False)
        self.__graph.enableAutoRange(axis='y', enable=False)
        self.__graph.setLimits(xMin=0, xMax=5000, yMin=-10, yMax=200)
        self.__graph.setRange(xRange=[-10, 600], yRange=[-10, 20])
        self.__graph.setLabel('left', 'deviation', units='σ', unitPrefix='')
        self.__graph.setLabel('bottom', 'velocity', units='osu!px/s', unitPrefix='')
        self.__graph.addLegend()

        # Deviation marker indicating expected deviation according to set CS
        self.__dev_marker_95 = pyqtgraph.InfiniteLine(angle=0, movable=False, pen=pyqtgraph.mkPen(color=(255, 100, 0, 100), style=pyqtgraph.QtCore.Qt.DashLine))
        self.__graph.addItem(self.__dev_marker_95, ignoreBounds=True)

        self.__vel_marker = pyqtgraph.InfiniteLine(angle=90, movable=False, pen=pyqtgraph.mkPen(color=(200, 200, 0, 100), style=pyqtgraph.QtCore.Qt.DashLine))
        self.__graph.addItem(self.__vel_marker, ignoreBounds=True)

        self.__dx = None
        self.__bpm = None

        # Used to set text in legend item
        self.__label_style = pyqtgraph.PlotDataItem(pen=(0,0,0))
        self.__graph.getPlotItem().legend.addItem(self.__label_style, '')
        self.__text = self.__graph.getPlotItem().legend.getLabel(self.__label_style)
        
        # Interactive region plot to the right to select distance between notes in data
        self.__px_plot = pyqtgraph.PlotWidget()
        self.__px_plot.setXRange(-0.5, 0.5)
        self.__px_plot.setYRange(0, 520)
        self.__px_plot.getViewBox().setMouseEnabled(x=False, y=True)
        self.__px_plot.setLimits(yMin=-10, yMax=520)
        self.__px_plot.enableAutoRange(axis='x', enable=False)
        self.__px_plot.enableAutoRange(axis='y', enable=False)
        self.__px_plot.hideAxis('bottom')
        self.__px_plot.hideAxis('left')
        self.__px_plot.showAxis('right')
        self.__px_plot.setFixedWidth(64)

        # Slider region allowing to select distance between notes
        self.__px_region = pyqtgraph.LinearRegionItem(values=(0, 10), orientation='horizontal')
        self.__px_region.setBounds((0, 512))
        self.__px_region.setRegion((0, 512))
        self.__px_region.sigRegionChanged.connect(lambda: StddevGraphVel.__px_region_event(self))

        # Label for the interactive region plot
        self.__px_label = QtGui.QLabel('    Dist')
        self.__px_label.setStyleSheet('background-color: black')

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

        # Put it all together
        self.__ang_plot.addItem(self.__ang_region)
        self.__px_plot.addItem(self.__px_region)
        self.__rot_plot.addItem(self.__rot_region)

        self.__ang_layout = QtGui.QVBoxLayout()
        self.__ang_layout.setSpacing(0)
        self.__ang_layout.addWidget(self.__ang_plot)
        self.__ang_layout.addWidget(self.__ang_label)

        self.__px_layout = QtGui.QVBoxLayout()
        self.__px_layout.setSpacing(0)
        self.__px_layout.addWidget(self.__px_plot)
        self.__px_layout.addWidget(self.__px_label)

        self.__rot_layout = QtGui.QVBoxLayout()
        self.__rot_layout.setSpacing(0)
        self.__rot_layout.addWidget(self.__rot_plot)
        self.__rot_layout.addWidget(self.__rot_label)

        self.__layout = QtGui.QHBoxLayout(self.graphs[self.__id]['widget'])
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(2)
        self.__layout.addWidget(self.__graph)
        self.__layout.addLayout(self.__ang_layout)
        self.__layout.addLayout(self.__px_layout)
        self.__layout.addLayout(self.__rot_layout)
        

    def plot_data(self, data):
        if data.shape[0] == 0:
            return

        # Clear plots for redraw
        self.__graph.clearPlots()
        self.__text.setText(f'')

        # Select data slices by angle
        ang0, ang1 = self.__ang_region.getRegion()
        ang_select = ((ang0 <= data[:, self.COL_ANGLE]) & (data[:, self.COL_ANGLE] <= ang1))

        # Select data slices by distance
        px0, px1 = self.__px_region.getRegion()
        px_select = ((px0 <= data[:, self.COL_PX]) & (data[:, self.COL_PX] <= px1))

        # Select data slices by rotation
        rot0, rot1 = self.__rot_region.getRegion()
        rot_select = ((rot0 <= data[:, self.COL_ROT]) & (data[:, self.COL_ROT] <= rot1))

        unique_angs = np.unique(data[:, self.COL_ANGLE])
        self.__ang_plot.clearPlots()
        self.__ang_plot.plot(np.zeros(unique_angs.shape[0]), unique_angs, pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')

        unique_pxs = np.unique(data[:, self.COL_PX])
        self.__px_plot.clearPlots()
        self.__px_plot.plot(np.zeros(unique_pxs.shape[0]), unique_pxs, pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')

        unique_rots = np.unique(data[:, self.COL_ROT])
        self.__rot_plot.clearPlots()
        self.__rot_plot.plot(np.zeros(unique_rots.shape[0]), unique_rots, pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')

        # Colored gradient r->g->b multiple plots at different angles
        unique_angs = np.unique(data[ang_select & rot_select, self.COL_ANGLE])
        if unique_angs.shape[0] == 0:
            # Data selection empty
            return

        angle_lut = pyqtgraph.ColorMap(
            np.linspace(min(unique_angs), max(unique_angs), 3),
            np.array(
                [
                    [  0, 100, 255, 200],
                    [100, 255, 100, 200],
                    [255, 100, 100, 200],
                ]
            )
        )

        # Adds a plot for every unique BPM recorded
        for angle in unique_angs:
            # Determine data selected by angle
            ang_select = (data[:, self.COL_ANGLE] == angle)
            data_select = ang_select & px_select & rot_select
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

            # Plot color
            color = angle_lut.map(angle, 'qcolor')

            # Calc linear regression
            m, b = Utils.linear_regresion(vels, stdevs)
            if type(m) == type(None) or type(b) == type(None):
                self.__graph.plot(x=vels, y=stdevs, pen=None, symbol='o', symbolPen=None, symbolSize=10, symbolBrush=color)
                continue

            y_model = m*vels + b      
            label = f'∠={angle:.2f}  σ={np.std(stdevs - y_model):.2f}  m={m:.5f}  b={b:.2f}'

            if self.model_compensation:
                self.__graph.plot(x=vels, y=stdevs - y_model, pen=None, symbol='o', symbolPen=None, symbolSize=10, symbolBrush=color, name=label)
                self.__graph.plot(x=[0, max(vels)], y=[0, 0], pen=(100, 100, 0, 150))
            else:
                self.__graph.plot(x=vels, y=stdevs, pen=None, symbol='o', symbolPen=None, symbolSize=10, symbolBrush=color, name=label)
                self.__graph.plot(x=[0, max(vels)], y=[b, m*max(vels) + b], pen=(100, 100, 0, 150))  

    
    def __angle_region_event(self):
        # When the selection on angle plot changes, reprocess main graph
        StddevGraphVel.plot_data(self, self.data)
    
    
    def __px_region_event(self):
        # When the selection on distance plot changes, reprocess main graph
        StddevGraphVel.plot_data(self, self.data)


    def __rot_region_event(self):
        # When the selection on rotation plot changes, reprocess main graph
        StddevGraphVel.plot_data(self, self.data)


    def set_dev(self, dev):
        self.__dev_marker_95.setPos(dev/4)


    def update_vel(self, dx=None, bpm=None):
        if type(dx) != type(None):
            self.__dx = dx

        if type(bpm) != type(None):
            self.__bpm = bpm

        if type(self.__dx) != type(None) and type(self.__bpm) != type(None):
            self.__vel_marker.setPos(self.__dx*self.__bpm/60)