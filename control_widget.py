from PyQt5.QtWidgets import (QWidget, QGridLayout, QLabel, QSpinBox,
                             QDoubleSpinBox, QComboBox, QPushButton,
                             QGroupBox, QHBoxLayout, QVBoxLayout,
                             QCheckBox, QFrame, QSplitter)
from PyQt5.QtCore import pyqtSignal, Qt
import math

from basic_custom_widget.QEngLineEdit import QEngLineEdit
from basic_custom_widget.QSwitchButton import QSwitchButton

from pathlib import Path

class ControlWidget(QWidget):
    # 任何参数改动都发这个信号，dict 携带最新值
    params_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._build_ui()
        self._connect_signals()

    # ---------- 构建 ----------
    def _build_ui(self):
        self.setMinimumWidth(320)
        self.setMaximumWidth(500)
        layout = QVBoxLayout(self)

        # 0.设备设置
        devgrp = QGroupBox("Device Settings")
        h = QGridLayout(devgrp)
        self.device_type = QComboBox()
        self.device_type.addItems(["VNA","E-M"])
        self.device_m_model = QComboBox()
        self.device_m_model.addItems(["SVA1000X","SSA3000X"])
        self.device_e_model = QComboBox()
        self.device_e_model.addItems(["EM1000","EM2000"])
        self.device_m_address = QEngLineEdit()
        self.device_e_address = QEngLineEdit()
        self.device_tunnel = QComboBox()
        self.device_tunnel.addItems(["VISA","Socket","Serial"])

        h.addWidget(QLabel("Type"),0,0)
        h.addWidget(self.device_type,0,1)
        h.addWidget(QLabel("M-Model"),1,0)
        h.addWidget(self.device_m_model,1,1)
        h.addWidget(QLabel("M-Address"),2,0)
        h.addWidget(self.device_m_address,2,1)
        h.addWidget(QLabel("E-Model"),3,0)
        h.addWidget(self.device_e_model,3,1)
        h.addWidget(QLabel("E-Address"),4,0)
        h.addWidget(self.device_e_address,4,1)
        h.addWidget(QLabel("Tunnel"),5,0)
        h.addWidget(self.device_tunnel,5,1)
    
        layout.addWidget(devgrp)

        # 1. 频率设置
        fgrp = QGroupBox("Frequency")
        g = QVBoxLayout(fgrp)
        titlehbox = QHBoxLayout()
        grid_layout_frequency_set = QGridLayout()
        hbox_sweep_set = QHBoxLayout()
        hbox_no_of_points = QHBoxLayout()

        self.sweep_fixed_button = QSwitchButton()

        self.sp_fstart = QEngLineEdit(alignment=Qt.AlignRight,suffix="Hz")
        self.sp_fstart.setValue(10)
        
        self.sp_fstop = QEngLineEdit(alignment=Qt.AlignRight,suffix="Hz")
        self.sp_fstop.setValue(1000000)

        self.sp_fcenter = QEngLineEdit(alignment=Qt.AlignRight,suffix="Hz")
        self.sp_fcenter.setValue(500005)

        self.sp_fspan = QEngLineEdit(alignment=Qt.AlignRight,suffix="Hz")
        self.sp_fspan.setValue(999990)

        self.sp_points = QSpinBox()
        self.sp_points.setRange(3, 10001)
        self.sp_points.setValue(201)
        self.sp_points.setSingleStep(10)

        self.get_from_zoom_btn = QPushButton("Get From Zoom")
        
        self.sweep_log_switch = QSwitchButton()

        hbox_no_of_points.addWidget(QLabel("Number of Points"))
        hbox_no_of_points.addWidget(self.sp_points)

        titlehbox.addWidget(QLabel("Frequency"),3)
        titlehbox.addWidget(QLabel("Sweep"),1)
        titlehbox.addWidget(self.sweep_fixed_button,1)
        titlehbox.addWidget(QLabel("Fixed"),1)

        grid_layout_frequency_set.addWidget(QLabel("Start Frequency"), 0, 0)
        grid_layout_frequency_set.addWidget(self.sp_fstart, 0, 1)
        grid_layout_frequency_set.addWidget(QLabel("Stop Frequency"), 1, 0)
        grid_layout_frequency_set.addWidget(self.sp_fstop, 1, 1)
        grid_layout_frequency_set.addWidget(QLabel("Center"), 2, 0)
        grid_layout_frequency_set.addWidget(self.sp_fcenter, 2, 1)
        grid_layout_frequency_set.addWidget(QLabel("Span"), 3, 0)
        grid_layout_frequency_set.addWidget(self.sp_fspan, 3, 1)

        hbox_sweep_set.addWidget(QLabel("Sweep"),3)
        hbox_sweep_set.addWidget(QLabel("Linear"),1)
        hbox_sweep_set.addWidget(self.sweep_log_switch,1)
        hbox_sweep_set.addWidget(QLabel("Log"),1)

        g.addLayout(titlehbox)
        g.addLayout(grid_layout_frequency_set)
        g.addWidget(self.get_from_zoom_btn)
        g.addLayout(hbox_sweep_set)
        g.addLayout(hbox_no_of_points)
        layout.addWidget(fgrp)

        # 2. 激励幅度
        levelgpb = QGroupBox("Level")
        h = QVBoxLayout(levelgpb)
        hb_var_switch = QHBoxLayout()
        hb_level = QHBoxLayout()
        hb_level_unit = QHBoxLayout()

        self.level_var_switch = QSwitchButton()
        self.level_unit_cb = QComboBox()
        self.level_unit_cb.addItems(["V","W","dBm"])
        self.level_unit_cb.setCurrentIndex(2)
        self.source_level = QEngLineEdit(alignment=Qt.AlignRight,suffix=self.level_unit_cb.currentText())
        self.source_level.setValue(0)

        hb_var_switch.addWidget(QLabel("Level"),3)
        hb_var_switch.addWidget(QLabel("Constant"),1)
        hb_var_switch.addWidget(self.level_var_switch)
        hb_var_switch.addWidget(QLabel("Variable"),1)

        hb_level.addWidget(QLabel("Source Level"))
        hb_level.addWidget(self.source_level)

        hb_level_unit.addWidget(QLabel("Level Unit"))
        hb_level_unit.addWidget(self.level_unit_cb)

        h.addLayout(hb_var_switch)
        h.addLayout(hb_level)
        h.addLayout(hb_level_unit)

        layout.addWidget(levelgpb)

        # 3. 衰减器
        srcgrp = QGroupBox("Attenuator")
        g = QHBoxLayout(srcgrp)
        g_att = QGridLayout()

        self.receive1_att = QComboBox()
        self.receive1_att.addItems(["0 dB", "10 dB","20 dB","30 dB","40 dB"])
        self.receive2_att = QComboBox()
        self.receive2_att.addItems(["0 dB", "10 dB","20 dB","30 dB","40 dB"])

        g.addWidget(QLabel("Attenuator"))

        g_att.addWidget(QLabel("Receiver 1"),0,0)
        g_att.addWidget(self.receive1_att,1,0)
        g_att.addWidget(QLabel("Receiver 2"),0,1)
        g_att.addWidget(self.receive2_att,1,1)

        g.addLayout(g_att)

        layout.addWidget(srcgrp)

        # 4. RBW
        curgrp = QGroupBox("Receiver Bandwidth")
        h = QHBoxLayout(curgrp)
        self.cb_bw = QComboBox()
        self.cb_bw.addItems(["1 Hz", "3 Hz", "5 Hz", "10 Hz", "30 Hz", "50 Hz","100 Hz", "300 Hz", "500 Hz", "1 kHz", "3 kHz", "5 kHz"])
        self.cb_bw.setCurrentText("300 Hz")
        h.addWidget(QLabel("Receiver Bandwidth"))
        h.addWidget(self.cb_bw)
        layout.addWidget(curgrp)

        layout.addStretch()

        self._device_model_refresh()

    # ---------- 信号 ----------
    def _connect_signals(self):
        # 数值型控件
        for w in [self.sp_fstart, self.sp_fstop, self.sp_points, self.source_level, self.sp_fspan,self.sp_fcenter]:
            w.valueChanged.connect(self._notify)
        # line edit
        for w in [self.device_m_address, self.device_e_address]:
            w.textChanged.connect(self._notify)
        # device type/model/tunnel
        self.device_type.currentTextChanged.connect(self._device_model_refresh)
        # 下拉框
        for w in [ self.cb_bw, self.level_unit_cb, self.receive1_att, self.receive2_att,self.device_type,self.device_m_model,self.device_e_model,self.device_tunnel]:
            w.currentTextChanged.connect(self._notify)
        # switch button
        for w in [self.sweep_log_switch, self.level_var_switch, self.sweep_fixed_button]:
            w.toggled.connect(self._notify)
        self.level_unit_cb.currentTextChanged.connect(self._unit_refresh)
        # 频率计算迭代控件
        for w in [self.sp_fstart, self.sp_fstop, self.sp_fspan,self.sp_fcenter]:
            w.valueChanged.connect(self._source_level_update)

    def _source_level_update(self):
        for w in [self.sp_fstart, self.sp_fstop, self.sp_fspan,self.sp_fcenter]:
            w.valueChanged.disconnect(self._source_level_update)
        sender = self.sender()
        fstart=self.sp_fstart.value()
        fstop=self.sp_fstop.value()
        fspan=self.sp_fspan.value()
        fcenter=self.sp_fcenter.value()
        if( sender == self.sp_fcenter or sender == self.sp_fspan ):
            fstartx=(fcenter-fspan/2) if (fcenter-fspan/2)>0 else 0.001
            self.sp_fstart.setValue(fstartx)
            self.sp_fstop.setValue(fcenter+fspan/2)
        if(sender == self.sp_fstart or sender == self.sp_fstop):
            self.sp_fspan.setValue(fstop-fstart)
            self.sp_fcenter.setValue((fstop+fstart)/2)
        for w in [self.sp_fstart, self.sp_fstop, self.sp_fspan,self.sp_fcenter]:
            w.valueChanged.connect(self._source_level_update)

    def _unit_refresh(self):
        v=self.source_level.value()
        self.source_level.setSuffix(self.level_unit_cb.currentText())
        self.source_level.setValue(v)

    def _device_model_refresh(self):
        model=self.device_m_model.currentText()
        dtype=self.device_type.currentText()
        VNA_path = Path('./xDriver/VNA_Class/')
        EM_E_path = Path('./xDriver/EM_Class/Excitation/')
        EM_M_path = Path('./xDriver/EM_Class/Measurement/')
        if dtype=="VNA":
            files = [f.stem for f in VNA_path.glob('*.py') if f.is_file() and f.stem != '__init__']
            self.device_m_model.clear()
            self.device_m_model.addItems(files)
            self.device_e_model.clear()
            self.device_e_model.setEnabled(False)
            self.device_e_address.setEnabled(False)
        elif dtype=="E-M":
            files_M = [f.stem for f in EM_M_path.glob('*.py') if f.is_file() and f.stem != '__init__']
            files_E = [f.stem for f in EM_E_path.glob('*.py') if f.is_file() and f.stem != '__init__']
            self.device_e_address.setEnabled(True)
            self.device_e_model.setEnabled(True)
            self.device_m_model.clear()
            self.device_m_model.addItems(files_M)
            self.device_e_model.clear()
            self.device_e_model.addItems(files_E)
        if model in [self.device_m_model.itemText(i) for i in range(self.device_m_model.count())]:
            self.device_m_model.setCurrentText(model)
        self._notify()

    def _notify(self):
        d = dict(
            device_m_address=self.device_m_address.text(),
            device_e_address=self.device_e_address.text(),
            device_type=self.device_type.currentText(),
            device_m_model=self.device_m_model.currentText(),
            device_e_model=self.device_e_model.currentText(),
            device_tunnel=self.device_tunnel.currentText(),
            sweep_fixed = self.sweep_fixed_button.isOn(),
            fstart=self.sp_fstart.value(),
            fstop=self.sp_fstop.value(),
            fspan=self.sp_fspan.value(),
            fcenter=self.sp_fcenter.value(),
            sweep_mode = self.sweep_log_switch.isOn(),
            points=self.sp_points.value(),
            level_variable = self.level_var_switch.isOn(),
            level_unit = self.level_unit_cb.currentText(),
            level = self.source_level.value(),
            recev1_att = self.receive1_att.currentText(),
            recev2_att = self.receive2_att.currentText(),
            rbw=self.cb_bw.currentText(),
        )
        print(d)
        self.params_changed.emit(d)