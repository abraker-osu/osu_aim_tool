import pyqtgraph
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore

import numpy as np
import math

from osu_analysis import BeatmapIO, ReplayIO, StdMapData, StdReplayData, Gamemode

from app.misc._utils import Utils
from app.misc._osu_utils import OsuUtils
from app.misc._hitobject_plot import HitobjectPlot
from app.misc._timing_plot import TimingPlot
from app.config import AppConfig


class PatternVisual(QtGui.QWidget):

    MAP_T = 0
    MAP_X = 1
    MAP_Y = 2

    REPLAY_T = 0
    REPLAY_X = 1
    REPLAY_Y = 2
    REPLAY_K1 = 3
    REPLAY_K2 = 4
    REPLAY_M1 = 5
    REPLAY_M2 = 6

    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.map_data    = np.asarray([])
        self.replay_data = np.asarray([])

        self.map_data_x = None
        self.map_data_y = None
        self.map_data_t = None

        self.map_md5 = None
        self.ar_ms = None
        self.cs_px = None

        self.replay_data_x  = None
        self.replay_data_y  = None
        self.replay_data_t  = None
        self.replay_data_k1 = None
        self.replay_data_k2 = None
        self.replay_data_m1 = None
        self.replay_data_m2 = None

        self.replay_data = None

        self.__init_gui()
        self.__build_layout()


    def __init_gui(self):
        self.menu_bar  = QtGui.QMenuBar()
        self.file_menu = QtGui.QMenu("&File")

        self.open_map_action    = QtGui.QAction("&Open *.osu", self.file_menu, triggered=lambda: self.__open_map())
        self.open_replay_action = QtGui.QAction("&Open *.osr", self.file_menu, triggered=lambda: self.__open_replay())

        self.layout = QtGui.QVBoxLayout(self)

        # Pattern Visualization
        self.visual = pyqtgraph.PlotWidget(title='Pattern visualization')
        self.plot_hits = self.visual.plot(title='Hit scatter', pen=None, symbol='o', symbolPen=None, symbolSize=100, symbolBrush=(100, 100, 255, 200), pxMode=False)
        self.plot_approach = self.visual.plot(pen=None, symbol='o', symbolPen=(100, 100, 255, 200), symbolBrush=None, symbolSize=100, pxMode=False)
        
        # Timing visualization
        self.timeline = pyqtgraph.PlotWidget()
        self.timeline_marker = pyqtgraph.InfiniteLine(angle=90, movable=True)
        self.hitobject_plot = HitobjectPlot()
        self.k1_timing_plot = TimingPlot()
        self.k2_timing_plot = TimingPlot()
        self.m1_timing_plot = TimingPlot()
        self.m2_timing_plot = TimingPlot()

        self.cursor_plot = self.visual.plot(pen=None, symbol='o', symbolPen='y', symbolBrush=None, symbolSize=2, pxMode=True)


    def __build_layout(self):
        self.setWindowTitle('osu! Aim Tool Pattern Visualization')

        self.menu_bar.addMenu(self.file_menu)
        self.file_menu.addAction(self.open_map_action)
        self.file_menu.addAction(self.open_replay_action)

        self.layout.addWidget(self.menu_bar)
        self.layout.addWidget(self.visual)
        self.layout.addWidget(self.timeline)

        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.visual.showGrid(True, True)
        self.visual.setXRange(0, 540)
        self.visual.setYRange(-410, 0)
        #self.visual.getViewBox().setMouseEnabled(x=False, y=False)
        self.visual.enableAutoRange(axis='x', enable=False)
        self.visual.enableAutoRange(axis='y', enable=False)

        self.timeline.setFixedHeight(64)
        self.timeline.getViewBox().setMouseEnabled(y=False)
        self.timeline.hideAxis('left')
        self.timeline.setXRange(-1, 4)
        self.timeline.setYRange(-5, 5)

        self.timeline_marker.setBounds((-10000, None))
        self.timeline_marker.sigPositionChanged.connect(self.__time_changed_event)

        self.timeline.addItem(self.timeline_marker, ignoreBounds=True)
        self.timeline.addItem(self.hitobject_plot)
        self.timeline.addItem(self.k1_timing_plot)
        self.timeline.addItem(self.k2_timing_plot)
        self.timeline.addItem(self.m1_timing_plot)
        self.timeline.addItem(self.m2_timing_plot)
        self.__time_changed_event()


    def set_map(self, data_x, data_y, data_t, cs, ar, md5=None):
        if type(data_x) == type(None): return
        if type(data_y) == type(None): return
        if type(data_t) == type(None): return

        if type(ar) == type(None): return
        if type(cs) == type(None): return        

        self.map_data = np.zeros((len(data_x), 3))
        self.map_data[:, self.MAP_T] = data_t
        self.map_data[:, self.MAP_X] = data_x
        self.map_data[:, self.MAP_Y] = data_y

        self.cs_px = OsuUtils.cs_to_px(cs)
        self.ar_ms = OsuUtils.ar_to_ms(ar)/1000
        self.map_md5 = md5

        self.__draw_map_data()
        

    def set_replay(self, replay_data):
        if type(replay_data) == type(None): 
            return

        self.replay_data = np.zeros((len(replay_data['time']), 7))
        self.replay_data[:, self.REPLAY_T]  = np.asarray(replay_data['time'])/1000
        self.replay_data[:, self.REPLAY_X]  = np.asarray(replay_data['x'])
        self.replay_data[:, self.REPLAY_Y]  = -np.asarray(replay_data['y'])
        self.replay_data[:, self.REPLAY_K1] = np.asarray(replay_data['k1'])
        self.replay_data[:, self.REPLAY_K2] = np.asarray(replay_data['k2'])
        self.replay_data[:, self.REPLAY_M1] = np.asarray(replay_data['m1'])
        self.replay_data[:, self.REPLAY_M2] = np.asarray(replay_data['m2'])

        self.__draw_replay_data()
        

    def __draw_map_data(self):
        if type(self.map_data) == type(None): 
            return

        if type(self.ar_ms) == type(None): return
        if type(self.cs_px) == type(None): return

        map_data_t = self.map_data[:, self.MAP_T]
        map_data_x = self.map_data[:, self.MAP_X]
        map_data_y = self.map_data[:, self.MAP_Y]

        ar_select = (self.t <= map_data_t) & (map_data_t <= (self.t + self.ar_ms))

        self.plot_hits.setData(map_data_x[ar_select], map_data_y[ar_select], symbolSize=self.cs_px)

        sizes = OsuUtils.approach_circle_to_radius(self.cs_px, self.ar_ms, map_data_t[ar_select] - self.t)
        self.plot_approach.setData(map_data_x[ar_select], map_data_y[ar_select], symbolSize=sizes)
        self.visual.update()

        self.hitobject_plot.setMap(map_data_t, map_data_t, np.full_like(map_data_t, StdMapData.TYPE_SLIDER))
        self.timeline.update()
        

    def __draw_replay_data(self):
        if type(self.replay_data) == type(None):
            return

        replay_data_t = self.replay_data[:, self.REPLAY_T]

        select_time = (replay_data_t >= self.t - 0.05) & (replay_data_t <= self.t)
        replay_data_x = self.replay_data[select_time, self.REPLAY_X]
        replay_data_y = self.replay_data[select_time, self.REPLAY_Y]
        
        self.cursor_plot.setData(replay_data_x, replay_data_y, symbolPen=(255, 255, 0, 100))
        self.visual.update()

        k1_press_select = self.replay_data[:, self.REPLAY_K1] == StdReplayData.PRESS
        k2_press_select = self.replay_data[:, self.REPLAY_K2] == StdReplayData.PRESS
        m1_press_select = self.replay_data[:, self.REPLAY_M1] == StdReplayData.PRESS
        m2_press_select = self.replay_data[:, self.REPLAY_M2] == StdReplayData.PRESS

        k1_release_select = self.replay_data[:, self.REPLAY_K1] == StdReplayData.RELEASE
        k2_release_select = self.replay_data[:, self.REPLAY_K2] == StdReplayData.RELEASE
        m1_release_select = self.replay_data[:, self.REPLAY_M1] == StdReplayData.RELEASE
        m2_release_select = self.replay_data[:, self.REPLAY_M2] == StdReplayData.RELEASE        

        self.timeline.removeItem(self.k1_timing_plot)
        self.k1_timing_plot = TimingPlot()
        self.k1_timing_plot.setTimings(
            self.replay_data[k1_press_select, self.REPLAY_T], 
            self.replay_data[k1_release_select, self.REPLAY_T], 
            y_pos=-4, color=(255, 100, 100, 150)
        )
        self.timeline.addItem(self.k1_timing_plot)

        self.timeline.removeItem(self.m1_timing_plot)
        self.m1_timing_plot = TimingPlot()
        self.m1_timing_plot.setTimings(
            self.replay_data[m1_press_select, self.REPLAY_T], 
            self.replay_data[m1_release_select, self.REPLAY_T], 
            y_pos=-2, color=(255, 100, 255, 150)
        )
        self.timeline.addItem(self.m1_timing_plot)

        self.timeline.removeItem(self.k2_timing_plot)
        self.k2_timing_plot = TimingPlot()
        self.k2_timing_plot.setTimings(
            self.replay_data[k2_press_select, self.REPLAY_T], 
            self.replay_data[k2_release_select, self.REPLAY_T], 
            y_pos=2, color=(71, 185, 255, 150)
        )
        self.timeline.addItem(self.k2_timing_plot)

        self.timeline.removeItem(self.m2_timing_plot)
        self.m2_timing_plot = TimingPlot()
        self.m2_timing_plot.setTimings(
            self.replay_data[m2_press_select, self.REPLAY_T], 
            self.replay_data[m2_release_select, self.REPLAY_T], 
            y_pos=4, color=(100, 255, 100, 150)
        )
        self.timeline.addItem(self.m2_timing_plot)

        self.timeline.update()


    def __time_changed_event(self):
        self.t = self.timeline_marker.getPos()[0]
        self.__draw_map_data()
        self.__draw_replay_data()


    def __open_map(self):
        file_name = QtGui.QFileDialog.getOpenFileName(self, 'Open file',  f'{AppConfig.cfg["osu_dir"]}/Songs', 'osu! map files (*.osu)')
        file_name = file_name[0]

        if len(file_name) == 0:
            return

        try: beatmap = BeatmapIO.open_beatmap(file_name)
        except Exception as e:
            print(Utils.get_traceback(e, 'Error opening map'))
            return

        if beatmap.gamemode != Gamemode.OSU:
            print(f'{Gamemode(beatmap.gamemode)} gamemode is not supported')
            return

        try: map_data = StdMapData.get_map_data(beatmap)
        except Exception as e:
            print(Utils.get_traceback(e, 'Error reading map'))
            return

        presses = StdMapData.get_presses(map_data)

        map_data_t = presses['time']/1000
        map_data_x = presses['x']
        map_data_y = -presses['y'] 

        self.set_map(map_data_x, map_data_y, map_data_t, beatmap.difficulty.cs, beatmap.difficulty.ar, beatmap.metadata.beatmap_md5)


    def __open_replay(self):
        name_filter = 'osu! replay files (*.osr)' if self.map_md5 == None else f'osu! replay files ({self.map_md5}-*.osr)'

        file_name = QtGui.QFileDialog.getOpenFileName(self, 'Open replay',  f'{AppConfig.cfg["osu_dir"]}/Data/r', name_filter)
        file_name = file_name[0]

        if len(file_name) == 0:
            return

        try: self.replay = ReplayIO.open_replay(file_name)
        except Exception as e:
            print(Utils.get_traceback(e, 'Error opening replay'))
            return

        try: replay_data = StdReplayData.get_replay_data(self.replay)
        except Exception as e:
            print(Utils.get_traceback(e, 'Error reading replay'))
            return

        self.set_replay(replay_data)

        
