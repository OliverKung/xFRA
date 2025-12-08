# -*- coding: utf-8 -*-
import sys
from typing import List, Dict, Any
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGroupBox, QComboBox, QSpinBox,
    QLineEdit, QCheckBox, QLabel, QHBoxLayout, QVBoxLayout,
    QGridLayout, QStackedWidget, QPushButton
)
# 顶部导入区补一行
from PyQt5.QtCore import pyqtSignal   # <-- 新增

from basic_custom_widget.QLabelComboBox import QLabelComboBox
from basic_custom_widget.QIconButtonWidget import QIconButtonWidget
from basic_custom_widget.QLabelLineEdit import QLabelLineEdit


# ==================================================================
#  单个 Trace 配置面板
# ==================================================================
class TraceConfigWidget(QGroupBox):
    trace_config_changed = pyqtSignal(dict)
    def __init__(self, title: str = "", parent=None):
        super().__init__(title, parent)
        self._trace_list: List[str] = []
        self._init_ui()

    def get_config(self) -> Dict[str, Any]:
        # ---------- 外部接口：返回当前配置 ----------
        cfg = {
            "meas_type"    : self.lcb_meas.currentText(),
            "category"     : self.lcb_category.currentText(),
            "expression"   : self.le_expression.text(),
            "format"       : self.lcb_fmt.currentText(),
        }

        meas_type = self.lcb_meas.currentText()
        if meas_type == "Meas":
            category_type = self.lcb_category.currentText()
            if category_type == "Imped":
                cfg["expression"] = "z11"
            elif category_type == "Refl":
                cfg["expression"] = "s11"
            elif category_type == "Gain":
                cfg["expression"] = "s21"
            elif category_type == "Admit":
                cfg["expression"] = "1/z11"
        else:
            pass  # 继续往下取参数
        
        format = self.lcb_fmt.currentText()
        if format == "Mag":
            cfg["expression"] = "abs({})".format(cfg["expression"])
        elif format == "Mag(dB)":
            cfg["expression"] = "20*log10(abs({}))".format(cfg["expression"])
        elif format == "Phase(°)":
            cfg["expression"] = "phase({})*180/pi".format(cfg["expression"])
        elif format == "Phase(Rad)":
            cfg["expression"] = "phase({})".format(cfg["expression"])
        elif format == "Tg":
            cfg["expression"] = "tan(phase({}))".format(cfg["expression"])
        elif format == "Real":
            cfg["expression"] = "real({})".format(cfg["expression"])
        elif format == "Imag":
            cfg["expression"] = "imag({})".format(cfg["expression"])
        else:
            pass

        cfg.update({
            "unwrap_phase" : self.checkbox_unwrap_phase.isChecked(),
            "x_axis_scale" : self.lcb_x_axis_scale.currentText(),
            "y_suffix"     : self.unit_suffix_lineedit.text(),
        })
        return cfg
    # ------ 内部 UI ------
    def _init_ui(self):
        # 顶部固定行
        self.top = QVBoxLayout()
        self._init_meas()
        self._init_fmt()

        # 动态大页（Measurement 部分）
        self._stack = QStackedWidget()
        self._build_meas_page()          # 初始建页
        self._stack.setCurrentIndex(0)

        # 整体布局
        main = QVBoxLayout(self)
        main.addLayout(self.top)
        main.addWidget(self._stack)

        # 信号
        self.lcb_meas.currentTextChanged.connect(self._on_meas_changed)
        self.lcb_fmt.currentTextChanged.connect(self._on_fmt_changed)
        self.lcb_datasource.currentTextChanged.connect(self._on_datasource_changed)
        self._connect_signals()
        # self.setMaximumHeight(350)   # 数字随意

    # ---------- 初始化Measurement ---------
    def _init_meas(self):
        self.lcb_datasource = QLabelComboBox( # lcb stands for LabelComboBox
            label_text="Data Source",
            combo_items=["Meas", "SNP File"]
        )
        self.snp_file_path = QLabelLineEdit(label_text="SNP File Path")
        self.lcb_meas = QLabelComboBox(# lcb stands for LabelComboBox
            label_text="Measurement",
            combo_items=["Meas", "Expr"]
        )

        self.lcb_category = QLabelComboBox(# lcb stands for LabelComboBox
            label_text="Category",
            combo_items=["Imped", "Refl", "Gain", "Admit"]
        )

        self.le_expression = QLineEdit() #le stands for LineEdit

        self.top.addWidget(self.lcb_datasource)
        self.top.addWidget(self.snp_file_path)
        self.snp_file_path.setVisible(False)  # 默认隐藏 SNP File Path
        self.top.addWidget(self.lcb_meas)
        self.top.addWidget(self.lcb_category)
        self.top.addWidget(self.le_expression,3)

    # ---------- 初始化Format ---------
    def _init_fmt(self):
            # 1. 顶部固定：Format 下拉框
        self.lcb_fmt = QLabelComboBox(
            label_text="Format",
            combo_items=["Mag", "Mag(dB)", "Phase(°)", "Phase(Rad)", "Tg", "Real", "Imag"]
        )
        self.top.addWidget(self.lcb_fmt)

        # 2. 底部动态：用 QStackedWidget 管理
        self.lcb_x_axis_scale = QLabelComboBox(
            label_text="X-axis Scale",
            combo_items=["Log","Linear"]
        )
        self.top.addWidget(self.lcb_x_axis_scale)

        unit_suffix_hbox = QHBoxLayout()
        unit_suffix_hbox.addWidget(QLabel("Unit Suffix"))
        self.unit_suffix_lineedit = QLineEdit()
        unit_suffix_hbox.addWidget(self.unit_suffix_lineedit)
        self.top.addLayout(unit_suffix_hbox)

        phase_wrap_checkbox_hbox = QHBoxLayout()
        self.checkbox_unwrap_phase = QCheckBox("Unwrap Phase")
        phase_wrap_checkbox_hbox.addWidget(self.checkbox_unwrap_phase)
        self.top.addLayout(phase_wrap_checkbox_hbox)

        self.lcb_fmt.currentTextChanged.connect(self._on_fmt_changed)
        self._build_fmt_page()
    # ---------- 切换 Measurement ----------
    def _on_meas_changed(self):
        self._build_meas_page()

    def _build_meas_page(self):
        if self.lcb_meas.currentText() == "Meas":
            for w in [self.le_expression]:
                w.setVisible(False)
            self.lcb_category.setVisible(True)
        elif self.lcb_meas.currentText() == "Expr":
            for w in [self.lcb_category]:
                w.setVisible(False)
            for w in [self.le_expression]:
                w.setVisible(True)

    # ---------- 切换 Format（仅刷新底部一行） ----------
    def _on_fmt_changed(self):
        self._build_fmt_page()

    def _build_fmt_page(self):
        fmt = self.lcb_fmt.currentText()
        if fmt in ("Mag", "Real", "Imaginary", "Tg","Mag(dB)"):
            self.checkbox_unwrap_phase.setVisible(False)
            if self.unit_suffix_lineedit.text() in ("°", "Rad"):
                self.unit_suffix_lineedit.setText("")
        elif fmt in ("Phase(°)", "Phase(Rad)"):
            suffix = "°" if fmt == "Phase(°)" else "Rad"
            self.unit_suffix_lineedit.setText(suffix)
            self.checkbox_unwrap_phase.setVisible(True)
        else:
            return
    # ---------- 切换datasource ----------
    def _on_datasource_changed(self):
        if self.lcb_datasource.currentText() == "SNP File":
            self.snp_file_path.setVisible(True)
        else:
            self.snp_file_path.setVisible(False)
    def _on_any_change(self):
        self.trace_config_changed.emit(self.get_config())
        # 4. 在 _init_ui 末尾，把所有控件的信号连到统一槽
    def _connect_signals(self):
        # 顶部固定区
        self.lcb_meas.currentTextChanged.connect(self._on_any_change)
        self.lcb_category.currentTextChanged.connect(self._on_any_change)
        self.le_expression.textChanged.connect(self._on_any_change)

        # Format 下拉框
        self.lcb_fmt.currentTextChanged.connect(self._on_any_change)
        self.lcb_x_axis_scale.currentTextChanged.connect(self._on_any_change)
        self.unit_suffix_lineedit.textChanged.connect(self._on_any_change)
        self.checkbox_unwrap_phase.stateChanged.connect(self._on_any_change)