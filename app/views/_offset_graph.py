import numpy as np

import pyqtgraph
from pyqtgraph.Qt import QtGui

from app.misc._miss_plot import MissPlotItem
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

        self.__plot_hits = self.__graph.plot()
        self.__plot_rels = self.__graph.plot()

        self.__miss_plot = MissPlotItem()
        self.__graph.addItem(self.__miss_plot)

        self.__graph.addLine(x=None, y=0, pen=pyqtgraph.mkPen((0, 150, 0, 255), width=1))

        self.__offset_miss_pos_line = pyqtgraph.InfiniteLine(angle=0, pen=pyqtgraph.mkPen((255, 0, 0, 50), width=1))
        #self.__graph.addItem(self.__offset_miss_pos_line)

        self.__offset_miss_neg_line = pyqtgraph.InfiniteLine(angle=0, pen=pyqtgraph.mkPen((255, 0, 0, 50), width=1))
        #self.__graph.addItem(self.__offset_miss_neg_line)
        
        self.__offset_avg_line = pyqtgraph.InfiniteLine(angle=0, pen=pyqtgraph.mkPen((255, 255, 0, 150), width=1))
        self.__graph.addItem(self.__offset_avg_line)

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


    def plot_data(self, score_data):
        self.__plot_misses(score_data)
        self.__plot_hit_offsets(score_data)


    def set_window(self, neg_miss_win, pos_miss_win):
        self.__offset_miss_neg_line.setValue(neg_miss_win)
        self.__offset_miss_pos_line.setValue(pos_miss_win)


    def plot_data(self, play_data):
        if play_data.shape[0] == 0:
            return

        self.__plot_misses(play_data)
        self.__plot_hit_offsets(play_data)
        self.__plot_rel_offsets(play_data)
        self.__plot_avg_global(play_data)
        self.__update_hit_stats(play_data)


    def __plot_hit_offsets(self, data):
        # Extract timings and hit_offsets
        miss_filter = data['type'] != StdScoreData.TYPE_MISS
        prs_select  = data['action'] == StdScoreData.ACTION_PRESS
        select = prs_select & miss_filter
        
        if np.count_nonzero(select) == 0:
            self.__plot_hits.setData([], [], pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=(100, 100, 255, 200))
            return

        hit_timings = data['map_t'].values[select]
        hit_offsets = data['map_t'].values[select] - data['replay_t'].values[select]

        # Calculate view
        xMin = min(hit_timings) - 100
        xMax = max(hit_timings) + 100

        # Set plot data
        self.__plot_hits.setData(hit_timings, hit_offsets, pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=(100, 100, 255, 200))
        self.__graph.setLimits(xMin=xMin - 100, xMax=xMax + 100)
        self.__graph.setRange(xRange=[ xMin - 100, xMax + 100 ])


    def __plot_rel_offsets(self, data):
        # Extract timings and hit_offsets
        miss_filter = data['type'] != StdScoreData.TYPE_MISS
        rel_select  = data['action'] == StdScoreData.ACTION_RELEASE
        select = rel_select & miss_filter

        if np.count_nonzero(select) == 0:
            self.__plot_rels.setData([], [], pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=(100, 100, 255, 200))
            return

        hit_timings = data['map_t'].values[select]
        hit_offsets = data['map_t'].values[select] - data['replay_t'].values[select]

        # Calculate view
        xMin = min(hit_timings) - 100
        xMax = max(hit_timings) + 100

        # Set plot data
        self.__plot_rels.setData(hit_timings, hit_offsets, pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=(105, 217, 255, 200))
        self.__graph.setLimits(xMin=xMin - 100, xMax=xMax + 100)
        self.__graph.setRange(xRange=[ xMin - 100, xMax + 100 ])


    def __plot_misses(self, data):
        # Extract data and plot
        miss_select = data['type'] == StdScoreData.TYPE_MISS
        hit_timings = data['map_t'].values[miss_select]

        self.__miss_plot.setData(hit_timings)


    def __plot_avg_global(self, data):
        # Extract timings and hit_offsets
        miss_filter = data['type'] != StdScoreData.TYPE_MISS
        hit_offsets = data['map_t'].values[miss_filter] - data['replay_t'].values[miss_filter]

        mean_offset = np.mean(hit_offsets)
        std_offset = np.std(hit_offsets)

        # Set plot data
        self.__offset_avg_line.setValue(mean_offset)
        self.__offset_std_line_pos.setValue(std_offset*2 + mean_offset)
        self.__offset_std_line_neg.setValue(-std_offset*2 + mean_offset)

        print(f'mean = {mean_offset:.2f} ms    std = {std_offset:.2f} ms')


    def __update_hit_stats(self, data):        
        free_misses = \
            (data['type'] == StdScoreData.TYPE_MISS) & \
            (data['action'] == StdScoreData.ACTION_FREE)
        num_free_misses = np.count_nonzero(free_misses)

        press_misses = \
            (data['type'] == StdScoreData.TYPE_MISS) & \
            (data['action'] == StdScoreData.ACTION_PRESS)
        num_press_misses = np.count_nonzero(press_misses)

        release_misses = \
            (data['type'] == StdScoreData.TYPE_MISS) & \
            (data['action'] == StdScoreData.ACTION_RELEASE)
        num_release_misses = np.count_nonzero(release_misses)

        hold_misses = \
            (data['type'] == StdScoreData.TYPE_MISS) & \
            (data['action'] == StdScoreData.ACTION_HOLD)
        num_hold_misses = np.count_nonzero(hold_misses)

        hits = \
            (data['type'] == StdScoreData.TYPE_HITP)
        data = data[hits]

        avg = self.__offset_avg_line.getPos()[1]
        dev = self.__offset_std_line_pos.getPos()[1] - avg

        self.hit_metrics.setText(
            f'''
            num free misses: {num_free_misses}
            num press misses: {num_press_misses}
            num release misses: {num_release_misses}
            num hold misses: {num_hold_misses}

            µ: {avg:.2f} ms
            2σ: ±{dev:.2f} ms    ({10*dev/2:.2f} UR)
            '''
        )

    def __on_view_range_changed(self, _=None):
        view = self.__graph.viewRect()
        pos_x = view.left()
        pos_y = view.bottom()

        margin_x = 0.001*(view.right() - view.left())
        margin_y = 0.001*(view.top() - view.bottom())

        self.hit_metrics.setPos(pos_x + margin_x, pos_y + margin_y)
