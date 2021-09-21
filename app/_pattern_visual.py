import pyqtgraph
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore

import numpy as np
import math


class PatternVisual():

    # Construct a unit radius circle for a graph
    class HitCircleFill(QtGui.QGraphicsObject):
        def __init__(self, center=(0.0, 0.0)):
            QtGui.QGraphicsObject.__init__(self)
            self.center = center
            self.radius = 1.0
            self.pen = pyqtgraph.mkPen(color=(255, 255, 255, 255), width=0.5)


        def boundingRect(self):
            rect = QtCore.QRectF(0, 0, 2*self.radius, 2*self.radius)
            rect.moveCenter(QtCore.QPointF(*self.center))
            return rect


        def paint(self, painter, option, widget):
            painter.setPen(self.pen)
            painter.drawEllipse(self.boundingRect())


    def __init__(self):
        self.data_x = None
        self.data_y = None
        self.data_t = None

        self.bpm   = None
        self.dx    = None
        self.angle = None
        self.rot   = None
        self.num   = None
        self.cs    = None
        self.ar    = None
        self.t     = None

        self.pattern_cache = False

        self.main_widget = QtGui.QWidget()
        self.layout = QtGui.QVBoxLayout(self.main_widget)
        self.visual = pyqtgraph.PlotWidget(title='Pattern visualization')
        self.timeline = pyqtgraph.PlotWidget()
        self.layout.addWidget(self.visual)
        self.layout.addWidget(self.timeline)

        #self.win_hits.setFixedSize(2*140, 2*140 + 32)

        self.plot_hits = self.visual.plot(title='Hit scatter', pen=None, symbol='o', symbolPen=None, symbolSize=100, symbolBrush=(100, 100, 255, 200), pxMode=False)
        self.visual.setXRange(-512, 512)
        self.visual.setYRange(-512, 512)
        self.visual.showGrid(True, True)
        #self.visual.getViewBox().setMouseEnabled(x=False, y=False)
        self.visual.enableAutoRange(axis='x', enable=False)
        self.visual.enableAutoRange(axis='y', enable=False)

        self.plot_approach = self.visual.plot(pen=None, symbol='o', symbolPen=(100, 100, 255, 200), symbolBrush=None, symbolSize=100, pxMode=False)
        
        #self.circle_item = AimGraph.HitCircle((0, 0))
        #self.visual.addItem(self.circle_item)

        self.timeline.setFixedHeight(64)
        self.timeline.hideAxis('left')

        # Interactive region item
        self.timeline_marker = pyqtgraph.InfiniteLine(angle=90, movable=True)
        self.timeline_marker.setBounds((-10000, None))
        self.timeline_marker.sigPositionChanged.connect(self.__time_changed_event)

        self.timeline.addItem(self.timeline_marker, ignoreBounds=True)
        self.__time_changed_event()


    def show(self):
        self.main_widget.show()


    def hide(self):
        self.main_widget.hide()


    def __set_cs(self, cs):
        cs_px = (109 - 9*cs)/2
        # TODO
        self.visual.update()


    def update(self, bpm=None, dx=None, angle=None, rot=None, num=None, cs=None, ar=None):
        if bpm == None:   bpm = self.bpm
        if dx == None:    dx = self.dx
        if angle == None: angle = self.angle
        if rot == None:   rot = self.rot
        if num == None:   num = self.num
        if cs == None:    cs = self.cs
        if ar == None:    ar = self.ar

        if bpm != self.bpm:     self.pattern_cache = False; self.bpm = bpm
        if dx != self.dx:       self.pattern_cache = False; self.dx = dx
        if angle != self.angle: self.pattern_cache = False; self.angle = angle
        if rot != self.rot:     self.pattern_cache = False; self.rot = rot
        if num != self.num:     self.pattern_cache = False; self.num = num
        if cs != self.cs:       self.pattern_cache = False; self.cs = cs
        if ar != self.ar:       self.pattern_cache = False; self.ar = ar

        if self.pattern_cache == False:
            self.__generate_pattern()
            self.__draw()
            self.visual.update()
                

    def __generate_pattern(self):
        _self = [ self.bpm, self.dx, self.angle, self.rot, self.num ]
        if None in _self:
            return

        ms_t = 60*1000/self.bpm
        rad  = math.pi/180

        p1x = (self.dx/2)*math.cos(rad*self.rot)
        p1y = (self.dx/2)*math.sin(rad*self.rot)

        p2x = -(self.dx/2)*math.cos(rad*self.rot)
        p2y = -(self.dx/2)*math.sin(rad*self.rot)

        p3x = self.dx*math.cos(rad*self.rot + rad*self.angle) + p2x
        p3y = self.dx*math.sin(rad*self.rot + rad*self.angle) + p2y

        px_cx = 1/3*(p1x + p2x + p3x)
        px_cy = 1/3*(p1y + p2y + p3y)

        p1x = int(p1x + 256 - px_cx)
        p1y = int(p1y + 192 - px_cy)
        
        p2x = int(p2x + 256 - px_cx)
        p2y = int(p2y + 192 - px_cy)

        p3x = int(p3x + 256 - px_cx)
        p3y = int(p3y + 192 - px_cy)

        self.data_x = np.tile([p1x, p2x, p3x, p2x], 1 + int(self.num/4))
        self.data_y = np.tile([-p1y, -p2y, -p3y, -p2y], 1 + int(self.num/4))
        self.data_t = np.arange(0, self.data_x.shape[0])*ms_t/1000

        self.pattern_cache = True


    def __draw(self):
        if type(self.data_x) == type(None): return
        if type(self.data_y) == type(None): return
        if type(self.data_t) == type(None): return

        if type(self.ar) == type(None): return
        if type(self.cs) == type(None): return

        if len(self.data_x) != len(self.data_y) != len(self.data_t):
            raise AssertionError('len(self.data_x) != len(self.data_y) != len(self.data_t)')

        ar_ms = self.ar_to_ms(self.ar)/1000
        ar_select = (self.t <= self.data_t) & (self.data_t <= (self.t + ar_ms))

        self.plot_hits.setData(self.data_x[ar_select], self.data_y[ar_select], symbolSize=self.cs_to_px(self.cs))

        sizes = self.approach_circle_to_radius(self.cs, self.ar, self.data_t[ar_select] - self.t)
        self.plot_approach.setData(self.data_x[ar_select], self.data_y[ar_select], symbolSize=sizes)


    def __time_changed_event(self):
        self.t = self.timeline_marker.getPos()[0]
        self.__draw()
        

    def ar_to_ms(self, ar):
        if ar <= 5: return 1800 - 120*ar
        else:       return 1950 - 150*ar

    
    def cs_to_px(self, cs):
        return (109 - 9*cs)

    
    def approach_circle_to_radius(self, cs, ar, dt):
        return self.cs_to_px(cs)*(1 + 3*dt/(self.ar_to_ms(ar)/1000))