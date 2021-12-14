from PyQt5 import QtCore, QtWidgets

from app.misc._custom_spinbox import CustomSpinBox


class ValueEdit(QtWidgets.QWidget):

    value_changed = QtCore.pyqtSignal(tuple)
    auto_value_changed = QtCore.pyqtSignal(tuple)

    def __init__(self, minimum, maximum, key, name, is_float=False, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)        

        self.key = key

        self.verticalLayout = QtWidgets.QVBoxLayout(self)

        if is_float:
            self.value = QtWidgets.QDoubleSpinBox(self)
            self.value.setDecimals(1)
        else:
            self.value = CustomSpinBox(self)
            self.value_changed.connect(lambda value: self.auto_value_changed.emit((self.key, value)))

        self.verticalLayout.addWidget(self.value)
        self.horizontalLayout = QtWidgets.QHBoxLayout()

        self.verticalLayout.addLayout(self.horizontalLayout)
        self.name_label = QtWidgets.QLabel(name)
        self.name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.horizontalLayout.addWidget(self.name_label)
        
        self.resize(self.sizeHint())

        self.value.valueChanged.connect(self.value_enter)
        self.value.textChanged.connect(self.__value_edit)
        self.value.setValue(0)
        self.value.setMaximum(maximum)
        self.value.setMinimum(minimum)

        #self.__update_style(self.value, 'Draggable', True)
        self.__is_error = False


    def set_value(self, value):
        self.value.setValue(value)
        self.value_enter()


    def get_value(self):
        return self.value.value()


    def is_error(self):
        return self.__is_error


    def __value_edit(self, _):
        self.__update_style(self.value, 'Unsaved', True)


    def __update_style(self, widget, key, val):
        widget.setProperty(key, val)

        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()


    def value_enter(self):
        self.__update_style(self.value, 'Unsaved', False)
        self.value_changed.emit((self.key, self.value.value()))


    def value_increase(self):
        if hasattr(self.value, 'auto_value_cache'):
            self.value.set_value(self.value.value() + self.value.auto_value_cache)