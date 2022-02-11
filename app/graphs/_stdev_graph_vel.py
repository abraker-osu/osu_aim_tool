import pyqtgraph
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore

import math
import numpy as np

from app.misc._utils import MathUtils
from app.misc._select_plot import SelectPlot


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
        self.__px_plot = SelectPlot(
            view_min = 0,  view_max = 512,
            val_min  = 0,  val_max  = 512,
            init_min = 75, init_max = 125,
            label = 'Dist',
            region_event = lambda: StddevGraphVel.__px_region_event(self),
            mouse_ctrl = True
        )

        # Interactive region plot to the right to select angle between notes in data
        self.__ang_plot = SelectPlot(
            view_min = 0, view_max = 180,
            val_min  = 0, val_max  = 180,
            init_min = 0, init_max = 180,
            label = 'Angle',
            region_event = lambda: StddevGraphVel.__angle_region_event(self)
        )

        # Interactive region plot to the right to select angle of rotation in data
        self.__rot_plot = SelectPlot(
            view_min = 0,  view_max = 180,
            val_min  = 0,  val_max  = 180,
            init_min = 0,  init_max = 30,
            label = 'Rot',
            region_event = lambda: StddevGraphVel.__rot_region_event(self)
        )

        # Put it all together
        self.__layout = QtGui.QHBoxLayout(self.graphs[self.__id]['widget'])
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(2)
        self.__layout.addWidget(self.__graph)
        self.__layout.addWidget(self.__ang_plot)
        self.__layout.addWidget(self.__px_plot)
        self.__layout.addWidget(self.__rot_plot)
        

    def plot_data(self, data):
        if data.shape[0] == 0:
            return

        DataRec = self.DataVer

        # Clear plots for redraw
        self.__graph.clearPlots()
        self.__text.setText(f'')

        # Select data slices by angle
        ang0, ang1 = self.__ang_plot.get_region()
        ang_select = ((ang0 <= data[:, DataRec.COL_ANGLE]) & (data[:, DataRec.COL_ANGLE] <= ang1))

        # Select data slices by distance
        px0, px1 = self.__px_plot.get_region()
        px_select = ((px0 <= data[:, DataRec.COL_PX]) & (data[:, DataRec.COL_PX] <= px1))

        # Select data slices by rotation
        rot0, rot1 = self.__rot_plot.get_region()
        rot_select = ((rot0 <= data[:, DataRec.COL_ROT]) & (data[:, DataRec.COL_ROT] <= rot1))

        unique_angs = np.unique(data[:, DataRec.COL_ANGLE])
        self.__ang_plot.plot(unique_angs)

        unique_pxs = np.unique(data[:, DataRec.COL_PX])
        self.__px_plot.plot(unique_pxs)

        unique_rots = np.unique(data[:, DataRec.COL_ROT])
        self.__rot_plot.plot(unique_rots)

        # Colored gradient r->g->b multiple plots at different angles
        unique_angs = np.unique(data[ang_select & rot_select & px_select, DataRec.COL_ANGLE])
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

        print()

        # Adds a plot for every unique BPM recorded
        for angle in unique_angs:
            # Determine data selected by angle
            ang_select = (data[:, DataRec.COL_ANGLE] == angle)
            data_select = ang_select & px_select & rot_select
            if not any(data_select):
                # Selected region has no data. Nothing else to do
                continue

            # Extract relavent data
            if self.dev_select == self.DEV_X:
                self.__graph.setTitle('Aim dev-x (vel)')
                stdevs = data[data_select, DataRec.COL_STDEV_X]
            elif self.dev_select == self.DEV_Y:
                self.__graph.setTitle('Aim dev-y (vel)')
                stdevs = data[data_select, DataRec.COL_STDEV_Y]
            elif self.dev_select == self.DEV_XY:
                self.__graph.setTitle('Aim dev-xy (vel)')
                stdevs = (data[data_select, DataRec.COL_STDEV_X]**2 + data[data_select, DataRec.COL_STDEV_Y]**2)**0.5
            elif self.dev_select == self.DEV_T:
                self.__graph.setTitle('Aim dev-t (vel)')
                stdevs = data[data_select, DataRec.COL_STDEV_T]
            elif self.dev_select == self.AVG_X:
                self.__graph.setTitle('Aim avg-x (bpm)')
                stdevs = data[data_select, DataRec.COL_AVG_X]
            elif self.dev_select == self.AVG_Y:
                self.__graph.setTitle('Aim avg-y (bpm)')
                stdevs = data[data_select, DataRec.COL_AVG_Y]
            elif self.dev_select == self.AVG_T:
                self.__graph.setTitle('Aim avg-t (bpm)')
                stdevs = data[data_select, DataRec.COL_AVG_T]

            pxs = data[data_select, DataRec.COL_PX]
            bpms = data[data_select, DataRec.COL_BPM]

            # Velocity
            vels = pxs*bpms/60

            # Plot color
            color = angle_lut.map(angle, 'qcolor')

            # Calc linear regression
            m, b = MathUtils.linear_regresion(vels, stdevs)
            if type(m) == type(None) or type(b) == type(None):
                self.__graph.plot(x=vels, y=stdevs, pen=None, symbol='o', symbolPen=None, symbolSize=5, symbolBrush=color)
                continue

            y_model = m*vels + b                # model: y = mx + b
            x_model = (stdevs - b)/m            # model: x = (y - b)/m

            m_dev_y = np.std(stdevs - y_model)  # deviation of y from model
            m_dev_x = np.std(vels - x_model)    # deviation of x from model

            x_mean = np.mean(vels)

            if m_dev_x == 0:
                self.__graph.plot(x=vels, y=stdevs, pen=None, symbol='o', symbolPen=None, symbolSize=5, symbolBrush=color, name=label)
                continue

            # Standard error of slope @ 95% confidence interval
            m_se_95 = (m_dev_y/m_dev_x)/math.sqrt(stdevs.shape[0] - 2)*1.96

            # Standard error of y-intercept @ 95% confidence interval
            b_se_95 = 2*m_se_95*x_mean

            label = f'∠={angle:.2f}  n={stdevs.shape[0]}  σ={m_dev_y:.2f}  m={m:.5f}±{m_se_95:.5f}  b={b:.2f}±{b_se_95:.2f}'
            print(f'velocity fit (y = mx+b): {label}')

            if self.model_compensation:
                self.__graph.plot(x=vels, y=stdevs - y_model, pen=None, symbol='o', symbolPen=None, symbolSize=5, symbolBrush=color, name=label)
                self.__graph.plot(x=[0, max(vels)], y=[0, 0], pen=(100, 100, 0, 150))
            else:
                self.__graph.plot(x=vels, y=stdevs, pen=None, symbol='o', symbolPen=None, symbolSize=5, symbolBrush=color, name=label)
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
