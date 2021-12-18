import pyqtgraph
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore

import numpy as np
import math

from osu_analysis import StdMapData

from app.misc._osu_utils import OsuUtils
from app.misc._hitobject_plot import HitobjectPlot


class PatternVisual():

    def __init__(self):
        self.data_x = None
        self.data_y = None
        self.data_t = None

        self.bpm   = None
        self.dx    = None
        self.angle = None
        self.rot   = None
        self.num   = None
        self.notes = None
        self.cs    = None
        self.ar    = None
        self.t     = None

        self.replay_data = None

        self.pattern_cache = False
        self.is_clip = False

        self.main_widget = QtGui.QWidget()
        self.main_widget.setWindowTitle('osu! Aim Tool Pattern Visualization')

        self.layout = QtGui.QVBoxLayout(self.main_widget)
        self.visual = pyqtgraph.PlotWidget(title='Pattern visualization')
        self.timeline = pyqtgraph.PlotWidget()

        self.layout.addWidget(self.visual)
        self.layout.addWidget(self.timeline)

        self.plot_hits = self.visual.plot(title='Hit scatter', pen=None, symbol='o', symbolPen=None, symbolSize=100, symbolBrush=(100, 100, 255, 200), pxMode=False)
        self.visual.showGrid(True, True)
        self.visual.setXRange(0, 540)
        self.visual.setYRange(-410, 0)
        #self.visual.getViewBox().setMouseEnabled(x=False, y=False)
        self.visual.enableAutoRange(axis='x', enable=False)
        self.visual.enableAutoRange(axis='y', enable=False)

        self.plot_approach = self.visual.plot(pen=None, symbol='o', symbolPen=(100, 100, 255, 200), symbolBrush=None, symbolSize=100, pxMode=False)
        
        self.timeline.setFixedHeight(64)
        self.timeline.getViewBox().setMouseEnabled(y=False)
        self.timeline.hideAxis('left')
        self.timeline.setXRange(-1, 4)

        # Interactive region item
        self.timeline_marker = pyqtgraph.InfiniteLine(angle=90, movable=True)
        self.timeline_marker.setBounds((-10000, None))
        self.timeline_marker.sigPositionChanged.connect(self.__time_changed_event)

        self.hitobject_plot = HitobjectPlot()
        self.cursor_plot    = self.visual.plot(pen=None, symbol='o', symbolPen='y', symbolBrush=None, symbolSize=2, pxMode=True)

        self.timeline.addItem(self.timeline_marker, ignoreBounds=True)
        self.timeline.addItem(self.hitobject_plot)
        self.__time_changed_event()


    def show(self):
        self.main_widget.show()


    def hide(self):
        self.main_widget.hide()


    def is_clipped(self):
        return self.is_clip


    def set_map(self, bpm=None, dx=None, angle=None, rot=None, num=None, notes=None, cs=None, ar=None):
        if bpm == None:   bpm = self.bpm
        if dx == None:    dx = self.dx
        if angle == None: angle = self.angle
        if rot == None:   rot = self.rot
        if num == None:   num = self.num
        if notes == None: notes = self.notes
        if cs == None:    cs = self.cs
        if ar == None:    ar = self.ar

        if bpm != self.bpm:     self.pattern_cache = False; self.bpm = bpm
        if dx != self.dx:       self.pattern_cache = False; self.dx = dx
        if angle != self.angle: self.pattern_cache = False; self.angle = angle
        if rot != self.rot:     self.pattern_cache = False; self.rot = rot
        if num != self.num:     self.pattern_cache = False; self.num = num
        if notes != self.notes: self.pattern_cache = False; self.notes = notes
        if cs != self.cs:       self.pattern_cache = False; self.cs = cs
        if ar != self.ar:       self.pattern_cache = False; self.ar = ar

        if self.pattern_cache == False:
            self.__generate_pattern()
            self.__draw_map_data()
            self.visual.update()


    def set_replay(self, replay_data):
        self.replay_data = replay_data
        
        self.__draw_replay_data()
        self.visual.update()


    def __generate_pattern(self):
        _self = [ self.bpm, self.dx, self.angle, self.rot, self.num, self.notes ]
        if None in _self:
            return

        pattern, self.is_clip = OsuUtils.generate_pattern2(self.rot*math.pi/180, self.dx, 60/self.bpm, self.angle*math.pi/180, self.notes, self.num)

        self.data_x = pattern[:, 0]
        self.data_y = -pattern[:, 1]
        self.data_t = pattern[:, 2]
        
        self.hitobject_plot.setMap(self.data_t, self.data_t, np.full_like(self.data_t, StdMapData.TYPE_SLIDER))

        self.pattern_cache = True


    def __draw_map_data(self):
        if type(self.data_x) == type(None): return
        if type(self.data_y) == type(None): return
        if type(self.data_t) == type(None): return

        if type(self.ar) == type(None): return
        if type(self.cs) == type(None): return

        if len(self.data_x) != len(self.data_y) != len(self.data_t):
            raise AssertionError('len(self.data_x) != len(self.data_y) != len(self.data_t)')

        cs_px = OsuUtils.cs_to_px(self.cs)
        ar_ms = OsuUtils.ar_to_ms(self.ar)/1000
        ar_select = (self.t <= self.data_t) & (self.data_t <= (self.t + ar_ms))

        self.plot_hits.setData(self.data_x[ar_select], self.data_y[ar_select], symbolSize=cs_px)

        sizes = OsuUtils.approach_circle_to_radius(cs_px, ar_ms, self.data_t[ar_select] - self.t)
        self.plot_approach.setData(self.data_x[ar_select], self.data_y[ar_select], symbolSize=sizes)


    def __draw_replay_data(self):
        if type(self.replay_data) == type(None): return

        replay_data_t = np.asarray(self.replay_data['time'])/1000
        replay_data_x = np.asarray(self.replay_data['x'])
        replay_data_y = -np.asarray(self.replay_data['y'])
        #replay_data_k1 = np.asarray(self.replay_data['k1'])
        #replay_data_k2 = np.asarray(self.replay_data['k2'])
        #replay_data_m1 = np.asarray(self.replay_data['m1'])
        #replay_data_m2 = np.asarray(self.replay_data['m2'])

        if len(replay_data_t) != len(replay_data_x) != len(replay_data_y):
            raise AssertionError('len(replay_data_t) != len(replay_data_x) != len(replay_data_y)')

        select_time = (replay_data_t >= self.t - 0.05) & (replay_data_t <= self.t)
        
        #color_map = {
        #   0 :  (255, 255, 0, 100),  # Yellow
        #   1 :  (  0, 255, 0, 200),  # Green
        #   2 :  (255,   0, 0, 200),  # Red
        #}

        #colors = [
        #    color_map[key] for key in self.replay_data_k[select_time]
        #]

        self.cursor_plot.setData(replay_data_x[select_time], replay_data_y[select_time], symbolPen=(255, 255, 0, 100))


    def __time_changed_event(self):
        self.t = self.timeline_marker.getPos()[0]
        self.__draw_map_data()
        self.__draw_replay_data()