import os
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType

path = os.path.dirname(os.path.abspath(__file__))
Ui_AboutReptateWindow, QDialog = loadUiType(os.path.join(path,'AboutDialog.ui'))

class AboutWindow(QDialog, Ui_AboutReptateWindow):
        def __init__(self, parent):
            super(AboutWindow, self).__init__(parent)
            self.setupUi(self)
