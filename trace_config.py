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


# ==================================================================
#  单个 Trace 配置面板
# ==================================================================
class TraceConfigWidget(QGroupBox):
    trace_config_changed = pyqtSignal(dict)
    def __init__(self, title: str = "", parent=None):
        super().__init__(title, parent)
        self._trace_list: List[str] = []
        self._init_ui()

    # ------ 外部接口 ------
    # ============================== TraceConfigWidget 新增 ==============================
    def set_config(self, cfg: dict):
        """
        一键还原界面状态
        参数cfg与get_config()返回格式完全一致
        """
        # 1. 顶部固定区
        self.lcb_meas.setCurrentText(cfg.get("meas_type", "Measurement"))
        self.lcb_category.setCurrentText(cfg.get("category", "Impedance"))
        self.le_expression.setText(cfg.get("expression", ""))

        # 2. Format 下拉框（会触发_on_fmt_changed，已自带）
        self.lcb_fmt.setCurrentText(cfg.get("format", "Mag"))

        # 3. 根据当前页把值刷进去
        idx = self.fmt_stack.currentIndex()
        if idx == 0:          # Mag / Real / Imaginary / Tg
            self.sb_Ymax_mag.setValue(cfg.get("y_max", 0))
            self.sb_Ymin_mag.setValue(cfg.get("y_min", 0))
            self.cb_scale_mag.setCurrentText(cfg.get("y_axis_scale", "Linear"))
        elif idx == 1:        # Mag(dB)
            self.sb_Ymax_db.setValue(cfg.get("y_max", 0))
            self.sb_Ymin_db.setValue(cfg.get("y_min", 0))
        elif idx == 2:        # Phase
            self.sb_Ymax_ph.setValue(cfg.get("y_max", 0))
            self.sb_Ymin_ph.setValue(cfg.get("y_min", 0))

        # 4. 统一发出一次信号，保证外部同步
        self.trace_config_changed.emit(self.get_config())

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

        # ------- 底部动态页由 QStackedWidget 管理，按需取值 -------
        idx = self.fmt_stack.currentIndex()
        if idx == 0:          # Mag / Real / Imaginary / Tg
            cfg.update({
                "unwrap_phase" : False,               # 本页无此控件
                "y_max"        : self.sb_Ymax_mag.value(),
                "y_min"        : self.sb_Ymin_mag.value(),
                "y_axis_scale" : self.cb_scale_mag.currentText(),
                "y_max_suffix" : "",
                "y_min_suffix" : "",
            })
        elif idx == 1:        # Mag(dB)
            cfg.update({
                "unwrap_phase" : False,
                "y_max"        : self.sb_Ymax_db.value(),
                "y_min"        : self.sb_Ymin_db.value(),
                "y_axis_scale" : "Linear",
                "y_max_suffix" : "dB",
                "y_min_suffix" : "dB",
            })
        elif idx == 2:        # Phase(°) / Phase(Rad)
            cfg.update({
                "unwrap_phase" : False,
                "y_max"        : self.sb_Ymax_ph.value(),
                "y_min"        : self.sb_Ymin_ph.value(),
                "y_axis_scale" : "Linear",
                "y_max_suffix" : self.sb_Ymax_ph.suffix(),
                "y_min_suffix" : self.sb_Ymin_ph.suffix(),
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
        self._connect_signals()
        self.setMaximumHeight(350)   # 数字随意

    # ---------- 初始化Measurement ---------
    def _init_meas(self):
        self.lcb_meas = QLabelComboBox(# lcb stands for LabelComboBox
            label_text="Measurement",
            combo_items=["Meas", "Expr"]
        )

        self.lcb_category = QLabelComboBox(# lcb stands for LabelComboBox
            label_text="Category",
            combo_items=["Imped", "Refl", "Gain", "Admit"]
        )

        self.le_expression = QLineEdit() #le stands for LineEdit

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
        self.fmt_stack = QStackedWidget()
        self.top.addWidget(self.fmt_stack)

        # ---- 预先把每一页做好 ----
        # 页 0：Mag / Real / Imaginary / Tg
        page_mag = QWidget()
        lay = QGridLayout(page_mag)
        self.sb_Ymax_mag = QSpinBox();  self.sb_Ymin_mag = QSpinBox()
        self.cb_scale_mag = QComboBox(); self.cb_scale_mag.addItems(["Linear", "Log"])
        lay.addWidget(QLabel("Ymax"),0,0); lay.addWidget(self.sb_Ymax_mag,0,1)
        lay.addWidget(QLabel("Ymin"),1,0); lay.addWidget(self.sb_Ymin_mag,1,1)
        lay.addWidget(QLabel("Y-axis Scale"),2,0); lay.addWidget(self.cb_scale_mag,2,1)
        self.fmt_stack.addWidget(page_mag)

        # 页 1：Mag(dB)
        page_db = QWidget()
        lay = QGridLayout(page_db)
        self.sb_Ymax_db = QSpinBox(); self.sb_Ymax_db.setSuffix("dB")
        self.sb_Ymin_db = QSpinBox(); self.sb_Ymin_db.setSuffix("dB")
        lay.addWidget(QLabel("Ymax"),0,0); lay.addWidget(self.sb_Ymax_db,0,1)
        lay.addWidget(QLabel("Ymin"),1,0); lay.addWidget(self.sb_Ymin_db,1,1)
        self.fmt_stack.addWidget(page_db)

        # 页 2：Phase ° / Rad
        page_phase = QWidget()
        lay = QGridLayout(page_phase)
        self.sb_Ymax_ph = QSpinBox(); self.sb_Ymin_ph = QSpinBox(); self.checkbox_unwrap_phase = QCheckBox()
        lay.addWidget(QLabel("Ymax"),0,0); lay.addWidget(self.sb_Ymax_ph,0,1)
        lay.addWidget(QLabel("Ymin"),1,0); lay.addWidget(self.sb_Ymin_ph,1,1)
        lay.addWidget(QLabel("Unwrap Phase"),2,0); lay.addWidget(self.checkbox_unwrap_phase,2,1)
        self.fmt_stack.addWidget(page_phase)

        # 信号
        self.lcb_fmt.currentTextChanged.connect(self._on_fmt_changed)
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
        if fmt in ("Mag", "Real", "Imaginary", "Tg"):
            self.fmt_stack.setCurrentIndex(0)
        elif fmt == "Mag(dB)":
            self.fmt_stack.setCurrentIndex(1)
        elif fmt in ("Phase(°)", "Phase(Rad)"):
            self.fmt_stack.setCurrentIndex(2)
            suffix = "°" if fmt == "Phase(°)" else "Rad"
            self.sb_Ymax_ph.setSuffix(suffix)
            self.sb_Ymin_ph.setSuffix(suffix)
        else:  # Polar / Nyquist / Nichols
            self.fmt_stack.setCurrentIndex(3)
        # 2. 外部接口：返回当前配置
    
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

        # 第 0 页：Mag / Real / Imaginary / Tg
        self.sb_Ymax_mag.valueChanged.connect(self._on_any_change)
        self.sb_Ymin_mag.valueChanged.connect(self._on_any_change)
        self.cb_scale_mag.currentTextChanged.connect(self._on_any_change)

        # 第 1 页：Mag(dB)
        self.sb_Ymax_db.valueChanged.connect(self._on_any_change)
        self.sb_Ymin_db.valueChanged.connect(self._on_any_change)

        # 第 2 页：Phase(°) / Phase(Rad)
        self.sb_Ymax_ph.valueChanged.connect(self._on_any_change)
        self.sb_Ymin_ph.valueChanged.connect(self._on_any_change)