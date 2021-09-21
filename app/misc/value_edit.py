from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import *



class ValueEdit(QWidget):

    value_changed = pyqtSignal(float)

    def __init__(self, minimum, maximum, ticks, name, is_float=False, parent=None):
        QWidget.__init__(self, parent=parent)        

        self.verticalLayout = QVBoxLayout(self)

        if is_float:
            self.value_label = QDoubleSpinBox(self)
            self.value_label.setDecimals(1)
        else:
            self.value_label = QSpinBox(self)

        self.verticalLayout.addWidget(self.value_label)
        self.horizontalLayout = QHBoxLayout()

        self.verticalLayout.addLayout(self.horizontalLayout)
        self.name_label = QLabel(name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.horizontalLayout.addWidget(self.name_label)
        
        self.resize(self.sizeHint())

        self.value_label.valueChanged.connect(self.value_enter)
        self.value_label.textChanged.connect(self.__value_edit)
        self.value_label.setValue(0)
        self.value_label.setMaximum(maximum)
        self.value_label.setMinimum(minimum)

        #self.__update_style(self.value_label, 'Draggable', True)
        self.__is_error = False


    def set_value(self, value):
        self.value_label.setValue(value)
        self.value_enter()


    def get_value(self):
        return self.value_label.value()


    def is_error(self):
        return self.__is_error


    def __value_edit(self, _):
        self.__update_style(self.value_label, 'Unsaved', True)


    def __update_style(self, widget, key, val):
        widget.setProperty(key, val)

        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()


    def value_enter(self):
        self.__update_style(self.value_label, 'Unsaved', False)
        self.value_changed.emit(self.value_label.value())