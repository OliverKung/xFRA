import os
import subprocess
import sys
#=============== MultiProcessing ===============#
from multiprocessing import Process, Queue
#===============PyQt5===============#
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, qApp,
                             QSplitter, QVBoxLayout, QWidget, QFileDialog, QSystemTrayIcon)
from PyQt5.QtCore import Qt,QTimer
from PyQt5.QtGui import QFont, QIcon

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
from utils.yaml_utils import yaml_dump, yaml_load

#=============== 主窗口 ===============#
import ctypes

class BodeAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file_path = None
        self.current_config_file = None
        self.meas_process = None
        # 针对每一条曲线都创建对应的s2pdata
        self.s2pdata = None
        self.trace_param = {}
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

    # ---------- Save / Save As ----------
    def _collect_config(self):
        from datetime import datetime
        config = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "device": self.ctrl.get_params(),
            "traces": list(self.trace.get_trace_params().values()),
            "file_path": self.file_path,
        }
        return config

    def _save(self):
        if self.current_config_file:
            self._write_config(self.current_config_file)
        else:
            self._save_as()

    def _save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration As",
            self.current_config_file or "./config.xfra",
            "xFRA Config (*.xfra);;YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if path:
            self._write_config(path)

    def _write_config(self, path):
        try:
            config = self._collect_config()
            yaml_str = yaml_dump(config)
            with open(path, "w", encoding="utf-8") as f:
                f.write(yaml_str)
            self.current_config_file = path
            fname = os.path.basename(path)
            self.setWindowTitle("xFRA - " + fname)
            print("Configuration saved to: " + path)
        except Exception as e:
            print("Failed to save configuration: " + str(e))

    def update_plot(self):
        self.trace_param = self.trace.get_trace_params()
        # if not self.s2pdata:
        #     print("No data loaded yet.")
        #     return
        # else:
        #     self.xConv.load_formulas(self.s2pdata, "xConv\\xConvFormulaDef.json") 
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
            # 读取S2P的数据
            s2pdata = self.load_s2p_file(trace_param['snp_file_path'])
            xConv= xConvFormulaTransformer()
            xConv.load_formulas(s2pdata, "xConv\\xConvFormulaDef.json")
            # 计算x_data和y_data
            x_data = s2pdata['freq']
            y_data = xConv.apply_formula(s2pdata, trace_param['expression'])
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
    # ---------- 读取文件，返回一个s2p数据字典 ----------
    def load_s2p_file(self, path: str):
        # 去除文件路径的拓展名
        base_path = os.path.splitext(path)[0]
        if not base_path.endswith('_RI'):
            print("Converting file to RI format using xConv...")
            os.system('python ./xConv/xConvSNPConverter.py {}'.format(path))
            reader = xConvS2PReader(base_path + '_RI.s2p')
        else:
            reader = xConvS2PReader(path)
        return reader.read()


    def _open_or_open_file(self):
        """Open a .xfra config file and restore all settings."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Configuration", "./",
            "xFRA Config (*.xfra *.yaml *.yml);;All Files (*)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                config = yaml_load(f.read())
            print("Configuration loaded from: " + path)
            self.current_config_file = path
            if "device" in config:
                self.ctrl.load_device_config(config["device"])
            if "traces" in config:
                self.trace.load_config(config["traces"])
            fname = os.path.basename(path)
            self.setWindowTitle("xFRA - " + fname)
            self.update_plot()
        except Exception as e:
            print("Failed to load configuration: " + str(e))
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
        print(d)
        # 检查d有无空元素
        # for k, v in d.items():
        #     if type (v) == str and v == "":
        #         if d['device_type'] == 'VNA' and k in ['device_e_model', 'device_e_address']:
        #             continue
        #         else:
        #             print(f"Parameter {k} is not set. Please check control panel.")
        #             return
        #     if v is None:
        #         print(f"Parameter {k} is not set. Please check control panel.")
        #         return
        print("Starting single measurement...")
        str_freq_list = ""
        str_amp_list = ""
        if d["level"]["level_variable"] == True:
            str_freq_list = ""
            str_amp_list = ""
            for point in d["level"]["level_var_points"]:
                str_freq_list += str([point[0]]).replace("[", "").replace("]", "") + ","
                str_amp_list += str(point[1]) + ","
        str_freq_list = str_freq_list[:-1]
        str_amp_list = str_amp_list[:-1]
        if d['type'] == 'VNA':
            cmd = None
            pass
            cmd = f'python .\\xDriver\\VNA_Class\\{d["device_m"]["model"]}.py --device-address {d["device_m"]["addr"]} ' + \
                    f'--device-tunnel {d["device_m"]["tunnel"]} --start-freq {d["freq"]["fstart"]} --stop-freq {d["freq"]["fstop"]} ' + \
                    f'--sweep-type {"LOG" if d["freq"]["sweep_mode"] else "LIN"} --sweep-points {d["freq"]["points"]} ' + \
                    f'--averages {d["average"]} --ifbw {d["ifbw"]} --source-level {d["level"]["level"]} --output-file .\\data\\measurement.s2p'
        elif d["type"] == 'E-M':
            cmd = None
            pass
            cmd = f"python .\\xDriver\\EM_Class\\xDrvEM.py" +\
                    f' --e-device-model {d["device_e"]["model"]} --m-device-model {d["device_m"]["model"]} ' +\
                    f' --e-device-tunnel {d["device_e"]["tunnel"]} --m-device-tunnel {d["device_m"]["tunnel"]} ' +\
                    f' --m-device-addr {d["device_m"]["addr"]} --e-device-addr {d["device_e"]["addr"]} ' +\
                    f' --average-sample-times {d["sample_method"]["average_times"]} --average {d["average"]} ' +\
                    f' --start-freq {d["freq"]["fstart"]} --end-freq {d["freq"]["fstop"]} ' +\
                    f' --sweep-type {"LOG" if d["freq"]["sweep_mode"] else "LIN"} --sweep-points {d["freq"]["points"]} ' +\
                    f' --ifbw {d["ifbw"]} ' +\
                    f' --source-amp {d["level"]["level"]} --source-amp-unit {d["level"]["level_unit"]} ' +\
                    f' --output-file .\\data\\measurement.s2p ' +\
                    f' --sample-method {d["sample_method"]["method"]} ' +\
                    f' --excition-channel {d["excitation"]["channel"]} ' +\
                    f' --input-channel {d["meas1"]["channel"]} ' +\
                    f' --output-channel {d["meas2"]["channel"]} ' +\
                    f' --sync-channel {d["syncMeas"]["channel"]} ' +\
                    f' --sync-trigger {d["syncExcit"]["channel"]} ' +\
                    f' --sync-trigger-enable {1 if d["syncExcit"]["enabled"] else 0} '
                    # f' --settling-time {d["settling_time"]} '

        if cmd is not None:
            # 新开一个进程，进程执行os.system(cmd)命令，以免阻塞主进程
            self.meas_process = subprocess.Popen(cmd, shell=True)
            print(f"Executing command: {cmd}")
            self.checkLifeTime.start(100)  # Check every second
            self.ribbon.stop_button.setEnabled(True)
            self.ribbon.single_meas_button.setEnabled(False)

    def check_lifetime(self):
        if self.meas_process.poll() is not None:  # Process has finished
            print("Measurement process finished.")
            self.checkLifeTime.stop()
            self.ribbon.stop_button.setEnabled(False)
            self.ribbon.single_meas_button.setEnabled(True)
            self.load_s2p_file(".\\data\\measurement.s2p")
            print("Data loaded successfully.")
            self.update_plot()

    def _stop_meas(self):
        """Stop the current single measurement."""
        if hasattr(self, 'meas_process') and self.meas_process is not None:
            self.meas_process.terminate()
            self.meas_process = None
        self.checkLifeTime.stop()
        self.ribbon.stop_button.setEnabled(False)
        self.ribbon.single_meas_button.setEnabled(True)
        print("Measurement stopped by user.")

    def _connect_signals(self):
        # ribbon 新建按钮 -> 刷新曲线
        self.ribbon.new_button.clicked.connect(self.plot.replot)
        # ribbon 打开按钮 -> 打开文件
        self.ribbon.open_button.clicked.connect(self._open_or_open_file)
        # ribbon 绘图按钮 -> 刷新曲线
        self.ribbon.plot_large_button.clicked.connect(self.update_plot)
        # ribbon 添加曲线按钮 -> 在trace widget中添加trace box
        self.ribbon.add_trace_btn.clicked.connect(lambda: self.trace.dw.add_box())
        # ribbon 添加math按钮 -> 在trace widget中添加math box
        self.ribbon.add_math_btn.setVisible(False)
        self.ribbon.add_math_btn.clicked.connect(lambda: self.trace.dw.add_box(box_type='math'))
        # ribbon 添加expression按钮 -> 在trace widget中添加expression box
        self.ribbon.add_expression_btn.clicked.connect(lambda: self.trace.dw.add_box(box_type='expression'))
        # ribbon 添加circuit fit按钮 -> 在trace widget中添加circuit fit box
        self.ribbon.add_circuit_fit_btn.clicked.connect(lambda: self.trace.dw.add_box(box_type='circuit_fit'))
        # 点击启动按钮，开始扫描
        self.ribbon.single_meas_button.clicked.connect(self._start_meas)
        self.ribbon.stop_button.clicked.connect(self._stop_meas)
        self.ribbon.save_button.clicked.connect(self._save)
        self.ribbon.save_as_button.clicked.connect(self._save_as)
        self.ribbon.report_button.clicked.connect(self.update_plot)
        # 控制面板改动 -> 刷新曲线
        self.trace.params_changed.connect(self.trace_params_changed)
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 设置托盘图标
    # app.setWindowIcon(QIcon("./icon/xFRA.png"))
    # tray_Icon = QSystemTrayIcon(QIcon("./icon/xFRA.png"), parent=app)
    # tray_Icon.show()
    # 设置任务栏图标
    font = QFont("Arial",10)
    app.setStyle("Fusion")
    app.setFont(font)
    w = BodeAnalyzer()
    w.setWindowIcon(QIcon("./icon/xFRA.png"))
    if(sys.platform == "win32"):
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u'myappid')
    w.show()
    sys.exit(app.exec_())