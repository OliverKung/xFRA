import os
import subprocess
import sys
#=============== MultiProcessing ===============#
from multiprocessing import Process, Queue
#===============PyQt5===============#
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, qApp,
                             QSplitter, QVBoxLayout, QWidget, QFileDialog)
from PyQt5.QtCore import Qt,QTimer
from PyQt5.QtGui import QFont

#===============Ribbon Bar===============#
from numpy import trace
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
        self.xConv = xConvFormulaTransformer()
        self.checkLifeTime = QTimer()
        self.checkLifeTime.timeout.connect(self.check_lifetime)
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
        if not self.s2pdata:
            print("No data loaded yet.")
            return
        else:
            self.xConv.load_formulas(self.s2pdata, "xConv\\xConvFormulaDef.json") 
        self.plot.remove_trace(wave_key="1")
        log_idx = 0
        lin_idx = 0
        
        # 清空plot_widget中所有的waveWidget
        self.plot.del_all_wave_widget()
        # 获取trace_param中的每一条trace信息，并按照x-axis类型添加到对应的waveWidget中
        for trace_param in self.trace_param.values():
            # 如果trace_param已被删除，则跳过
            if trace_param.get('deleted', False):
                continue
            # 计算x_data和y_data
            x_data = self.s2pdata['freq']
            y_data = self.xConv.apply_formula(self.s2pdata, trace_param['expression'])
            freq_axis = trace_param['x_axis_scale'].lower()
            # 根据坐标类型决定添加到哪个waveWidget
            if freq_axis == 'log':
                wave_key = f'log_{log_idx+1}'
                if wave_key not in self.plot.get_wave_widget_list():
                    self.plot.add_wave_widget(wave_key, freq_axis='log')
                log_idx += 1
            else:
                wave_key = f'lin_{lin_idx+1}'
                if wave_key not in self.plot.get_wave_widget_list():
                    self.plot.add_wave_widget(wave_key, freq_axis='lin')
                lin_idx += 1
            if trace_param['meas_type'] == 'Meas':
                trace_name = trace_param['category']+"_"+trace_param['format']
            else:
                trace_name = trace_param['expression']
            # 添加trace到对应的waveWidget
            self.plot.add_trace(
                wave_key=wave_key,
                name=trace_name,
                x_data=x_data,
                y_data=y_data,
                unit=trace_param['y_suffix'],
                label=trace_name,
                trace_color=trace_param['color']
            )

    def load_s2p_file(self, path: str):
        # 去除文件路径的拓展名
        self.file_path = path
        base_path = os.path.splitext(self.file_path)[0]
        if not base_path.endswith('_RI'):
            print("Converting file to RI format using xConv...")
            os.system('python ./xConv/xConvSNPConverter.py {}'.format(self.file_path))
            reader = xConvS2PReader(base_path + '_RI.s2p')
        else:
            reader = xConvS2PReader(self.file_path)
        self.s2pdata = reader.read()


    def open_file(self):
        # open the file select and save the file path to self.file_path
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Data File", "", "Data Files (*.csv *.txt *.s2p);;All Files (*)")
        if path:
            self.file_path = path
            print(f"File selected: {self.file_path}")
        try:
            self.load_s2p_file(self.file_path)
            print("Data loaded successfully")
        except Exception as e:
            print(f"Failed to load data: {e}")

    def _start_meas(self):
        d = self.ctrl.get_params()
        # 检查d有无空元素
        for k, v in d.items():
            if type (v) == str and v == "":
                if d['device_type'] == 'VNA' and k in ['device_e_model', 'device_e_address']:
                    continue
                else:
                    print(f"Parameter {k} is not set. Please check control panel.")
                    return
            if v is None:
                print(f"Parameter {k} is not set. Please check control panel.")
                return
        print("Starting single measurement...")
        if d['device_type'] == 'VNA':
            cmd = f'python .\\xDriver\\VNA_Class\\{d["device_m_model"]}.py --device-address {d["device_m_address"]} ' + \
                    f'--device-tunnel {d["device_tunnel"]} --start-freq {d["fstart"]} --stop-freq {d["fstop"]} ' + \
                    f'--sweep-type {"LOG" if d["sweep_mode"] else "LIN"} --sweep-points {d["points"]} ' + \
                    f'--averages {d["average"]} --ifbw {d["rbw"]} --source-level {d["level"]} --output-file .\\data\\measurement.s2p '
        if cmd is not None:
            # 新开一个进程，进程执行os.system(cmd)命令，以免阻塞主进程
            self.meas_process = subprocess.Popen(cmd, shell=True)
            # print(f"Executing command: {cmd}")
            self.checkLifeTime.start(100)  # Check every second

    def check_lifetime(self):
        if self.meas_process.poll() is not None:  # Process has finished
            print("Measurement process finished.")
            self.checkLifeTime.stop()
            self.load_s2p_file(".\\data\\measurement.s2p")
            print("Data loaded successfully.")
            self.update_plot()

    def _connect_signals(self):
        # ribbon 新建按钮 -> 刷新曲线
        self.ribbon.new_button.clicked.connect(self.plot.replot)
        # ribbon 打开按钮 -> 打开文件
        self.ribbon.open_button.clicked.connect(self.open_file)
        # ribbon 绘图按钮 -> 刷新曲线
        self.ribbon.plot_large_button.clicked.connect(self.update_plot)
        # 点击启动按钮，开始扫描
        self.ribbon.single_meas_button.clicked.connect(self._start_meas)
        # 控制面板改动 -> 刷新曲线
        self.trace.params_changed.connect(self.trace_params_changed)
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont("Arial",10)
    app.setStyle("Fusion")
    app.setFont(font)
    w = BodeAnalyzer()
    w.show()
    sys.exit(app.exec_())