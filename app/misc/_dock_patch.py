from pyqtgraph.dockarea.Dock import DockLabel


def updateStylePatched(self):
    if self.dim:
        self.setProperty('selected', False)
    else:
        self.setProperty('selected', True)

    if self.orientation == 'vertical':
        self.setProperty('orientation', 'vertical')
    else:
        self.setProperty('orientation', 'horizontal')

    self.style().unpolish(self)
    self.style().polish(self)
    self.update()

DockLabel.updateStyle = updateStylePatched