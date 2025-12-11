from PyQt5.QtWidgets import (QWidget, QGridLayout, QLabel, QSpinBox,
                             QDoubleSpinBox, QComboBox, QPushButton,
                             QGroupBox, QHBoxLayout, QVBoxLayout,
                             QCheckBox, QFrame, QSplitter,QLineEdit)
from PyQt5.QtCore import pyqtSignal, Qt
import math

from basic_custom_widget.QEngLineEdit import QEngLineEdit
from basic_custom_widget.QSwitchButton import QSwitchButton
from basic_custom_widget.QLabelComboBox import QLabelComboBox
from basic_custom_widget.QLabelLineEdit import QLabelLineEdit

from pathlib import Path
import chardet

class ControlWidget(QWidget):
    # 任何参数改动都发这个信号，dict 携带最新值
    params_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.VNA_path = Path('./xDriver/VNA_Class/')
        self.EM_E_path = Path('./xDriver/EM_Class/Excitation/')
        self.EM_M_path = Path('./xDriver/EM_Class/Measurement/')
        self._build_ui()
        self._connect_signals()

    # ---------- 构建 ----------
    def _build_ui(self):
        self.setMinimumWidth(320)
        self.setMaximumWidth(500)
        layout = QVBoxLayout(self)

        # 0.设备设置
        devgrp = QGroupBox("Device Settings")
        h = QVBoxLayout(devgrp)
        self.device_type = QLabelComboBox("Type")
        self.device_type.setComboItems(["VNA","E-M"])
        self.device_m_model = QLabelComboBox("M-Model")
        self.device_m_model.setComboItems(["SVA1000X","SSA3000X"])
        self.device_e_model = QLabelComboBox("E-Model")
        self.device_e_model.setComboItems(["EM1000","EM2000"])
        self.device_m_address = QLabelLineEdit("M-Address")
        self.device_e_address = QLabelLineEdit("E-Address")
        self.device_tunnel = QLabelComboBox("Tunnel")
        self.device_tunnel.setComboItems(["VISA","Socket","Serial"])

        h.addWidget(self.device_type)
        h.addWidget(self.device_m_model)
        h.addWidget(self.device_m_address)
        h.addWidget(self.device_e_model)
        h.addWidget(self.device_e_address)
        h.addWidget(self.device_tunnel)
    
        layout.addWidget(devgrp)

        # 1. 频率设置
        fgrp = QGroupBox("Frequency")
        g = QVBoxLayout(fgrp)
        titlehbox = QHBoxLayout()
        grid_layout_frequency_set = QGridLayout()
        hbox_sweep_set = QHBoxLayout()
        hbox_no_of_points = QHBoxLayout()

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
        self.level_unit_cb = QLabelComboBox("Level Unit")
        self.level_unit_cb.setComboItems(["V","W","dBm"])
        self.level_unit_cb.setCurrentIndex(2)
        self.source_level = QEngLineEdit(alignment=Qt.AlignRight,suffix=self.level_unit_cb.currentText())
        self.source_level.setValue(0)

        hb_var_switch.addWidget(QLabel("Level"),3)
        hb_var_switch.addWidget(QLabel("Constant"),1)
        hb_var_switch.addWidget(self.level_var_switch)
        hb_var_switch.addWidget(QLabel("Variable"),1)

        hb_level.addWidget(QLabel("Source Level"))
        hb_level.addWidget(self.source_level)

        hb_level_unit.addWidget(self.level_unit_cb)

        h.addLayout(hb_var_switch)
        h.addLayout(hb_level)
        h.addLayout(hb_level_unit)

        layout.addWidget(levelgpb)

        # 3. 衰减器
        srcgrp = QGroupBox("Attenuator")
        g = QVBoxLayout(srcgrp)

        self.receive1_att = QLabelComboBox("Recv 1")
        self.receive1_att.setComboItems(["0 dB", "10 dB","20 dB","30 dB","40 dB"])
        self.receive2_att = QLabelComboBox("Recv 2")
        self.receive2_att.setComboItems(["0 dB", "10 dB","20 dB","30 dB","40 dB"])

        g.addWidget(self.receive1_att)
        g.addWidget(self.receive2_att)

        layout.addWidget(srcgrp)
        
        # 4.平均测量
        avggrp = QGroupBox("Averaging")
        h = QHBoxLayout(avggrp)
        self.average_spinbox = QSpinBox()
        self.average_spinbox.setRange(1, 1000)
        self.average_spinbox.setValue(1)
        h.addWidget(QLabel("Averaging"),1)
        h.addWidget(self.average_spinbox,1)
        layout.addWidget(avggrp)

        # 5. RBW
        curgrp = QGroupBox("Receiver Bandwidth")
        h = QHBoxLayout(curgrp)
        self.cb_bw = QLabelComboBox("IF-BW")
        self.cb_bw.setComboItems(["1 Hz", "3 Hz", "5 Hz", "10 Hz", "30 Hz", "50 Hz","100 Hz", "300 Hz", "500 Hz", "1 kHz", "3 kHz", "5 kHz"])
        self.cb_bw.setCurrentText("300 Hz")
        h.addWidget(self.cb_bw)
        layout.addWidget(curgrp)

        layout.addStretch()

        self._device_model_refresh()
        self._update_model_setting()

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
        self.device_m_model.currentTextChanged.connect(self._update_model_setting)
        # 下拉框
        for w in [ self.cb_bw, self.level_unit_cb, self.receive1_att, self.receive2_att,self.device_type,self.device_m_model,self.device_e_model,self.device_tunnel]:
            w.currentTextChanged.connect(self._notify)
        # switch button
        for w in [self.sweep_log_switch, self.level_var_switch]:
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
        if dtype=="VNA":
            files = [f.stem for f in self.VNA_path.glob('*.py') if f.is_file() and f.stem != '__init__']
            self.device_m_model.setComboItems(files)
            self.device_e_model.setEnabled(False)
            self.device_e_address.setEnabled(False)
            self.device_e_address.setVisible(False)
            self.device_e_model.setVisible(False)
        elif dtype=="E-M":
            files_M = [f.stem for f in self.EM_M_path.glob('*.py') if f.is_file() and f.stem != '__init__']
            files_E = [f.stem for f in self.EM_E_path.glob('*.py') if f.is_file() and f.stem != '__init__']
            self.device_e_address.setEnabled(True)
            self.device_e_model.setEnabled(True)
            self.device_e_address.setVisible(True)
            self.device_e_model.setVisible(True)
            self.device_m_model.setComboItems(files_M)
            self.device_e_model.setComboItems(files_E)
        if model in [self.device_m_model.itemText(i) for i in range(self.device_m_model.count())]:
            self.device_m_model.setCurrentText(model)
        self._notify()

    def _update_model_setting(self):
        if self.device_type.currentText()=="VNA":
            str_VNA_path = self.VNA_path.as_posix() + '/'
            if self.device_m_model.currentText() == "":
                return
            with open(str_VNA_path+self.device_m_model.currentText()+'.py', 'rb') as f:
                raw_data = f.read()
                detected = chardet.detect(raw_data)
                encoding = detected['encoding']
            with open(str_VNA_path+self.device_m_model.currentText()+'.py', 'r',encoding=encoding) as f:
                fileLines = f.readlines()
                settingLine = []
                for line in fileLines:
                    if line.startswith('#'):
                        settingLine.append(line)
            xDrvSettingLine = False
            for line in settingLine:
                if line.startswith('# xDrvSetting begin'):
                    xDrvSettingLine = True
                elif line.startswith('# xDrvSetting end'):
                    xDrvSettingLine = False
                if xDrvSettingLine and not line.startswith('# xDrvSetting'):
                    command = line.strip().lstrip('#').strip()
                    if command.startswith('model'):
                        continue
                    elif command.startswith('tunnel'):
                        self.device_tunnel.setComboItems(command.split(' ')[1:])
                    elif command.startswith('average'):
                        if command.split(' ')[1].lower()=='yes':
                            self.average_spinbox.setEnabled(True)
                        else:
                            self.average_spinbox.setEnabled(False)
                            self.average_spinbox.setValue(1)
                    elif command.startswith('min-freq'):
                        min_freq = float(command.split(' ')[1])
                        self.sp_fstart.setLimits(min_value=min_freq)
                        self.sp_fstop.setLimits(min_value=min_freq)
                    elif command.startswith('max-freq'):
                        max_freq = float(command.split(' ')[1])
                        self.sp_fstart.setLimits(max_value=max_freq)
                        self.sp_fstop.setLimits(max_value=max_freq)
                    elif command.startswith('sweep-type'):
                        sweep_types = command.split(' ')[1:]
                        if 'LIN' in sweep_types and 'LOG' in sweep_types:
                            self.sweep_log_switch.setEnabled(True)
                        else:
                            self.sweep_log_switch.setEnabled(False)
                            if 'LIN' in sweep_types:
                                self.sweep_log_switch.setOn(False)
                            else:
                                self.sweep_log_switch.setOn(True)
                    elif command.startswith('sweep-points'):
                        self.sp_points.setRange(int(command.split(' ')[1]),int(command.split(' ')[2]))            
                    elif command.startswith('ifbw'):
                        self.cb_bw.setComboItems(command.split(' ')[1:])
                    elif command.startswith('variable-amp'):
                        if command.split(' ')[1].lower()=='yes':
                            self.level_var_switch.setEnabled(True)
                        else:
                            self.level_var_switch.setEnabled(False)
                            self.level_var_switch.setOn(False)
                    elif command.startswith('source-level'):
                        self.source_level.setLimits(float(command.split(' ')[1]),float(command.split(' ')[2]))
                    elif command.startswith('level-unit'):
                        self.level_unit_cb.setComboItems(command.split(' ')[1:])
                    elif command.startswith('Receiver1Attn'):
                        self.receive1_att.setComboItems([item+" dB" for item in command.split(' ')[1:]])
                    elif command.startswith('Receiver2Attn'):
                        self.receive2_att.setComboItems([item+" dB" for item in command.split(' ')[1:]])
        elif self.device_type.currentText()=="E-M":
            return
            # with open(self.EM_M_path / (self.device_m_model.currentText()+'.py'), 'r') as f:
            #     settingLine = f.readlines()

    def _notify(self):
        d = dict(
            device_m_address=self.device_m_address.text(),
            device_e_address=self.device_e_address.text(),
            device_type=self.device_type.currentText(),
            device_m_model=self.device_m_model.currentText(),
            device_e_model=self.device_e_model.currentText(),
            device_tunnel=self.device_tunnel.currentText(),
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
            average=self.average_spinbox.value()
        )
        # print(d)
        self.params_changed.emit(d)
    
    def get_params(self):
        d = dict(
            device_m_address=self.device_m_address.text(),
            device_e_address=self.device_e_address.text(),
            device_type=self.device_type.currentText(),
            device_m_model=self.device_m_model.currentText(),
            device_e_model=self.device_e_model.currentText(),
            device_tunnel=self.device_tunnel.currentText(),
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
            average=self.average_spinbox.value()
        )
        return d