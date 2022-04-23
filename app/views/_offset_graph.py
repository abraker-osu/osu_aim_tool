import numpy as np

import pyqtgraph
from pyqtgraph.Qt import QtGui

#from app.widgets.miss_plot import MissPlotItem
from osu_analysis import StdScoreData


class HitOffsetGraph(QtGui.QWidget):

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        # Main graph
        self.__graph = pyqtgraph.PlotWidget(title='Hit offset graph')
        self.__graph.getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.__graph.getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.__graph.enableAutoRange(axis='x', enable=False)
        self.__graph.enableAutoRange(axis='y', enable=False)
        self.__graph.setLimits(yMin=-200, yMax=200)
        self.__graph.setRange(xRange=[-10, 10000], yRange=[-250, 250])
        self.__graph.setLabel('left', 't-offset', units='ms', unitPrefix='')
        self.__graph.setLabel('bottom', 'time', units='ms', unitPrefix='')
        self.__graph.addLegend()

        self.__plot = self.__graph.plot()

        #self.__miss_plot = MissPlotItem()
        #self.__graph.addItem(self.__miss_plot)

        self.__graph.addLine(x=None, y=0, pen=pyqtgraph.mkPen((0, 150, 0, 255), width=1))

        self.__offset_miss_pos_line = pyqtgraph.InfiniteLine(angle=0, pen=pyqtgraph.mkPen((255, 0, 0, 50), width=1))
        self.__graph.addItem(self.__offset_miss_pos_line)

        self.__offset_miss_neg_line = pyqtgraph.InfiniteLine(angle=0, pen=pyqtgraph.mkPen((255, 0, 0, 50), width=1))
        self.__graph.addItem(self.__offset_miss_neg_line)
        
        #self.__offset_avg_line = pyqtgraph.InfiniteLine(angle=0, pen=pyqtgraph.mkPen((255, 255, 0, 150), width=1))
        #self.__graph.addItem(self.__offset_avg_line)

        self.__offset_std_line_pos = pyqtgraph.InfiniteLine(angle=0, pen=pyqtgraph.mkPen((255, 150, 0, 150), width=1))
        self.__offset_std_line_neg = pyqtgraph.InfiniteLine(angle=0, pen=pyqtgraph.mkPen((255, 150, 0, 150), width=1))

        self.__graph.addItem(self.__offset_std_line_pos)
        self.__graph.addItem(self.__offset_std_line_neg)

        # Hit stats
        self.hit_metrics = pyqtgraph.TextItem('', anchor=(0, 0), )
        self.__graph.addItem(self.hit_metrics)

        # Put it all together
        self.__layout = QtGui.QHBoxLayout(self)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(2)
        self.__layout.addWidget(self.__graph)

        self.__graph.sigRangeChanged.connect(self.__on_view_range_changed)
        self.__on_view_range_changed()


    def plot_data(self, hit_timings, hit_offsets):
        #self.__plot_misses(play_data)
        self.__plot_hit_offsets(hit_timings, hit_offsets)


    def set_window(self, neg_miss_win, pos_miss_win):
        self.__offset_miss_neg_line.setValue(neg_miss_win)
        self.__offset_miss_pos_line.setValue(pos_miss_win)


    def __plot_hit_offsets(self, hit_timings, hit_offsets):
        # Calculate view
        xMin = min(hit_timings) - 100
        xMax = max(hit_timings) + 100

        # Set plot data
        self.__plot.setData(hit_timings, hit_offsets, pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=(100, 100, 255, 200))
        self.__graph.setLimits(xMin=xMin - 100, xMax=xMax + 100)
        self.__graph.setRange(xRange=[ xMin - 100, xMax + 100 ])


    def __plot_misses(self, miss_timings):
        self.__miss_plot.setData(miss_timings)


    def __on_view_range_changed(self, _=None):
        view = self.__graph.viewRect()
        pos_x = view.left()
        pos_y = view.bottom()

        margin_x = 0.001*(view.right() - view.left())
        margin_y = 0.001*(view.top() - view.bottom())

        self.hit_metrics.setPos(pos_x + margin_x, pos_y + margin_y)
