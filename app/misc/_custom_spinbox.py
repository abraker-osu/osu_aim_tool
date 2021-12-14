from PyQt5 import QtCore, QtWidgets


# Thanks https://stackoverflow.com/a/55010348
class CustomSpinBox(QtWidgets.QSpinBox):

    value_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(CustomSpinBox, self).__init__(parent)

        self.auto_value_cache = 0


    def contextMenuEvent(self, event):
        QtCore.QTimer.singleShot(0, self.on_timeout)
        QtWidgets.QSpinBox.contextMenuEvent(self, event)


    def on_timeout(self):
        menu = self.findChild(QtWidgets.QMenu, 'qt_edit_menu')
        if menu is not None:
            value_widget = QtWidgets.QWidget()
            value_layout = QtWidgets.QHBoxLayout(value_widget)
            value_label  = QtWidgets.QLabel('Increase by:    ')
            value_edit   = QtWidgets.QSpinBox()

            value_edit.setValue(self.auto_value_cache)

            value_edit.valueChanged.connect(lambda: self.__value_changed_event(value_edit.value()))
            value_edit.textChanged.connect(lambda _: self.__value_changed_event(value_edit.value()))

            value_layout.addWidget(value_label)
            value_layout.addWidget(value_edit)
            value_layout.setContentsMargins(18, 4, 18, 4)
            value_layout.setAlignment(QtCore.Qt.AlignLeft)

            first_action = menu.actionAt(QtCore.QPoint())
            value_action = QtWidgets.QWidgetAction(menu)

            value_action.setDefaultWidget(value_widget)
            
            menu.insertAction(first_action, value_action)
            menu.insertSeparator(first_action)


    def __value_changed_event(self, value):
        self.auto_value_cache = value
        self.value_changed.emit(value)


    def set_auto_en(self, enabled):
        self.auto_chkbx_cache = enabled

    
    def set_auto_value(self, value):
        self.auto_value_cache = value