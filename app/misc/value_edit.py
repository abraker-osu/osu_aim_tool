from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QSlider, QSpacerItem, QVBoxLayout, QWidget



class ValueEdit(QWidget):

    value_changed = pyqtSignal(float)

    def __init__(self, minimum, maximum, ticks, name, is_float=False, parent=None):
        QWidget.__init__(self, parent=parent)

        self.verticalLayout = QVBoxLayout(self)
        self.value_label = QLineEdit(self)
        self.verticalLayout.addWidget(self.value_label)
        self.horizontalLayout = QHBoxLayout()

        self.verticalLayout.addLayout(self.horizontalLayout)
        self.name_label = QLabel(name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.verticalLayout.addWidget(self.name_label)
        self.resize(self.sizeHint())

        self.value_label.returnPressed.connect(self.value_enter)
        self.value_label.textEdited.connect(self.__value_edit)
        self.value_label.setText(str(0))

        self.__maximum = maximum
        self.__minimum = minimum

        self.__is_float = is_float
        self.__is_error = False


    def set_value(self, value):
        self.value_label.setText(str(value))
        self.value_enter()


    def get_value(self):
        if self.__is_float:
            return float(self.value_label.text())
        else:
            return int(float(self.value_label.text()))


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
        try:
            value = self.get_value()
            self.__update_style(self.value_label, 'Error', False)
            self.__is_error = False
        except ValueError:
            self.__update_style(self.value_label, 'Error', True)
            self.__is_error = True
            return

        self.__update_style(self.value_label, 'Unsaved', False)
        
        value = max(min(self.__maximum, value), self.__minimum)
        self.value_label.setText(f'{value}')
        self.value_changed.emit(value)