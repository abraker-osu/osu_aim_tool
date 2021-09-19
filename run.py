import sys
import json

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from app import App


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(open('stylesheet.css').read())
    
    ex  = App()
    sys.exit(app.exec_())