import os
import sys
from PyQt5.QtWidgets import QApplication

FULLPATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(FULLPATH)

from pyqt_win.main import MainWindow
if __name__ == '__main__':


    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
