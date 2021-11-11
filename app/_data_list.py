import re
import os

from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore



class DataList(QtGui.QListWidget):

    def __init__(self, app):
        QtGui.QListWidget.__init__(self)

        self.app = app
        self.selected_data_id = None
        self.data_list_ids = []

        self.setWindowTitle('Data file selection')

        self.currentRowChanged.connect(self.__data_list_click_event)
        

    def load_data_list(self):
        regex = re.compile(r'stdev_data_(\d+).npy')

        for data_file_name in os.listdir('data'):
            match = regex.match(data_file_name)
            if not match:
                continue
            
            self.data_list_ids.append(int(match.group(1)))
            self.addItem(data_file_name)


    def select_data_id(self, data_id):
        idx = self.data_list_ids.index(data_id)
        if idx == None:
            return

        self.setCurrentRow(idx)
        self.__data_list_click_event(idx)


    def __data_list_click_event(self, idx):
        selected_data_id = self.data_list_ids[idx]
        if self.selected_data_id == selected_data_id:
            return

        self.selected_data_id = selected_data_id
        self.app.load_data_file(selected_data_id)
        self.app.replot_graphs()
