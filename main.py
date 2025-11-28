import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, qApp,
                             QSplitter, QVBoxLayout, QWidget, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

#===============Ribbon Bar===============#
from pyqtribbon import RibbonBar

#===============用户widget===============#
from control_widget import ControlWidget
from plot_widget import PlotWidget
from trace_widget import TraceWidget
from custom_ribbon_bar import customRibbonBar

#===============加载xConv================#
from xConv.xConv import xConvS2PReader, xConvFormulaTransformer

class BodeAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file_path = None
        self.s2pdata = None
        self.setWindowTitle("xFRA - A Universal Frequency Response Analyzer ")
        self.resize(1920, 1080)
        self._create_menu()
        self._create_central()
        self._create_ribbonbar()
        self._connect_signals()

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


    # ---------- 中心控件 ----------
    def _create_central(self):
        splitter = QSplitter(Qt.Horizontal)

        self.ctrl = ControlWidget()
        self.plot = PlotWidget()
        self.trace = TraceWidget()

        splitter.addWidget(self.ctrl)
        splitter.addWidget(self.plot)
        splitter.addWidget(self.trace)
        splitter.setStretchFactor(1, 4)
        splitter.setStretchFactor(3, 4)
        self.setCentralWidget(splitter)
        
    def trace_params_changed(self, params: dict):
        return
    
    def update_plot(self):
        self.trace_param = self.trace.get_trace_params()
        
        print(self.trace_param)
        

    def open_file(self):
        # open the file select and save the file path to self.file_path
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Data File", "", "Data Files (*.csv *.txt *.s2p);;All Files (*)")
        if path:
            self.file_path = path
            print(f"File selected: {self.file_path}")
        try:
            reader = xConvS2PReader(self.file_path)
            self.s2pdata = reader.read()
            print(self.s2pdata)
            print("Data loaded successfully")
        except Exception as e:
            print(f"Failed to load data: {e}")


    def _connect_signals(self):
        # ribbon 新建按钮 -> 刷新曲线
        self.ribbon.new_button.clicked.connect(self.plot.replot)
        # ribbon 打开按钮 -> 打开文件
        self.ribbon.open_button.clicked.connect(self.open_file)
        # ribbon 绘图按钮 -> 刷新曲线
        self.ribbon.plot_large_button.clicked.connect(self.update_plot)
        # 控制面板改动 -> 刷新曲线
        self.trace.params_changed.connect(self.trace_params_changed)
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont("Arial",10)
    app.setStyle("Fusion")
    app.setFont(font)
    w = BodeAnalyzer()
    w.show()
    sys.exit(app.exec_())