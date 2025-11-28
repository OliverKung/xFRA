import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, qApp,
                             QSplitter, QVBoxLayout, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

#===============Ribbon Bar===============#
from pyqtribbon import RibbonBar

#===============用户widget===============#
from control_widget import ControlWidget
from plot_widget import PlotWidget
from trace_widget import TraceWidget
from custom_ribbon_bar import customRibbonBar

class BodeAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("xFRA - A Universal Frequency Response Analyzer ")
        self.resize(1920, 1080)
        self._create_menu()
        self._create_central()
        self._create_ribbonbar()

    # ---------- 菜单栏 ----------
    def _create_menu(self):
        bar = self.menuBar()
        file = bar.addMenu("File")
        for name, tip, short in [("New", "New measurement", "Ctrl+N"),
                                 ("Open", "Open file", "Ctrl+O"),
                                 ("Save", "Save", "Ctrl+S"),
                                 ("Save as", "Save as", "Ctrl+Shift+S"),
                                 ("Exit", "Exit application", "Ctrl+Q")]:
            act = QAction(name, self)
            act.setStatusTip(tip)
            if short == "Ctrl+Q":
                act.triggered.connect(qApp.quit)
            else:
                act.triggered.connect(lambda _, x=name: print(x, "clicked"))
            file.addAction(act)

        view = bar.addMenu("View")
        view.addAction("Cursor")
        view.addAction("Zoom")
        view.addAction("Unwrap phase")

    # ---------- ribbon bar控件 ----------
    def _create_ribbonbar(self):
        self.ribbon = customRibbonBar()
        self.setMenuBar(self.ribbon)
        self.ribbon.new_button.clicked.connect(self.plot.replot)

    # ---------- 中心控件 ----------
    def _create_central(self):
        splitter = QSplitter(Qt.Horizontal)

        self.ctrl = ControlWidget()
        self.plot = PlotWidget()
        self.trace = TraceWidget()

        # 控制面板改动 -> 刷新曲线
        # self.ctrl.params_changed.connect(self.plot.replot)

        splitter.addWidget(self.ctrl)
        splitter.addWidget(self.plot)
        splitter.addWidget(self.trace)
        splitter.setStretchFactor(1, 4)
        splitter.setStretchFactor(3, 4)
        self.setCentralWidget(splitter)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont("Arial",10)
    app.setStyle("Fusion")
    app.setFont(font)
    w = BodeAnalyzer()
    w.show()
    sys.exit(app.exec_())