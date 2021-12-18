import re
import os

from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore



class FloatingButtonWidget(QtGui.QPushButton):

    def __init__(self, parent):
        QtGui.QPushButton.__init__(self, parent)

        self.paddingLeft = 5
        self.paddingBottom = 5

        self.setFixedSize(32, 32)
        self.setIcon(self.style().standardIcon(QtGui.QStyle.SP_BrowserReload))


    def update_position(self):
        if hasattr(self.parent(), 'viewport'):
            parent_rect = self.parent().viewport().rect()
        else:
            parent_rect = self.parent().rect()

        if not parent_rect:
            return

        x = parent_rect.width() - self.width() - self.paddingLeft
        y = parent_rect.height() - self.height() - self.paddingBottom
        
        self.setGeometry(x, y, self.width(), self.height())


    def resizeEvent(self, event):
        QtGui.QPushButton.resizeEvent(self, event)
        self.update_position()



class DataList(QtGui.QListWidget):

    def __init__(self, app):
        QtGui.QListWidget.__init__(self)

        self.app = app
        self.selected_data_id = None
        self.data_list_ids = [] 

        self.data_file_regex = re.compile(r'stdev_data_(\d+).npy')

        self.refresh_btn = FloatingButtonWidget(parent=self)
        self.refresh_btn.clicked.connect(self.__refresh_btn_clicked)

        self.setWindowTitle('Data file selection')
        self.currentRowChanged.connect(self.__select_data_idx)
        

    def resizeEvent(self, event):
        QtGui.QListWidget.resizeEvent(self, event)
        self.refresh_btn.update_position()


    def load_data_list(self):
        self.clear()
        self.data_list_ids = []

        for data_file_name in os.listdir('data'):
            match = self.data_file_regex.match(data_file_name)
            if not match:
                continue
            
            self.data_list_ids.append(int(match.group(1)))
            self.addItem(data_file_name)        


    def select_data_id(self, data_id):
        idx = self.data_list_ids.index(data_id)
        if idx == None:
            return

        self.setCurrentRow(idx)
        self.__select_data_idx(idx)


    def __select_data_idx(self, idx):
        selected_data_id = self.data_list_ids[idx]
        if self.selected_data_id == selected_data_id:
            return

        self.selected_data_id = selected_data_id
        self.app.load_data_file(selected_data_id)
        self.app.replot_graphs()


    def __refresh_btn_clicked(self):
        self.blockSignals(True)
        self.load_data_list()
        self.blockSignals(False)

        self.select_data_id(self.selected_data_id)