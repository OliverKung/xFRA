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
        self.cat1_math.setCurrentText(cfg.get("math_cat1", "Measurement"))
        self.operator_math.setCurrentText(cfg.get("math_op", "+"))
        self.cat2_math.setCurrentText(cfg.get("math_cat2", "Measurement"))
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
        else:                 # Polar / Nyquist / Nichols
            self.sb_Ymax_pol.setValue(cfg.get("y_max", 0))
            self.sb_Ymin_pol.setValue(cfg.get("y_min", 0))
            self.sb_Xmax_pol.setValue(cfg.get("x_max", 0))
            self.sb_Xmin_pol.setValue(cfg.get("x_min", 0))

        # 4. 统一发出一次信号，保证外部同步
        self.trace_config_changed.emit(self.get_config())

    def get_config(self) -> Dict[str, Any]:
        # ---------- 外部接口：返回当前配置 ----------
        cfg = {
            "meas_type"    : self.lcb_meas.currentText(),
            "category"     : self.lcb_category.currentText(),
            "math_cat1"    : self.cat1_math.currentText(),
            "math_op"      : self.operator_math.currentText(),
            "math_cat2"    : self.cat2_math.currentText(),
            "expression"   : self.le_expression.text(),
            "format"       : self.lcb_fmt.currentText(),
        }

        # ------- 底部动态页由 QStackedWidget 管理，按需取值 -------
        idx = self.fmt_stack.currentIndex()
        if idx == 0:          # Mag / Real / Imaginary / Tg
            cfg.update({
                "unwrap_phase" : False,               # 本页无此控件
                "y_max"        : self.sb_Ymax_mag.value(),
                "y_min"        : self.sb_Ymin_mag.value(),
                "x_max"        : 0,
                "x_min"        : 0,
                "y_axis_scale" : self.cb_scale_mag.currentText(),
                "y_max_suffix" : "",
                "y_min_suffix" : "",
            })
        elif idx == 1:        # Mag(dB)
            cfg.update({
                "unwrap_phase" : False,
                "y_max"        : self.sb_Ymax_db.value(),
                "y_min"        : self.sb_Ymin_db.value(),
                "x_max"        : 0,
                "x_min"        : 0,
                "y_axis_scale" : "Linear",
                "y_max_suffix" : "dB",
                "y_min_suffix" : "dB",
            })
        elif idx == 2:        # Phase(°) / Phase(Rad)
            cfg.update({
                "unwrap_phase" : False,
                "y_max"        : self.sb_Ymax_ph.value(),
                "y_min"        : self.sb_Ymin_ph.value(),
                "x_max"        : 0,
                "x_min"        : 0,
                "y_axis_scale" : "Linear",
                "y_max_suffix" : self.sb_Ymax_ph.suffix(),
                "y_min_suffix" : self.sb_Ymin_ph.suffix(),
            })
        else:                 # Polar / Nyquist / Nichols
            cfg.update({
                "unwrap_phase" : False,
                "y_max"        : self.sb_Ymax_pol.value(),
                "y_min"        : self.sb_Ymin_pol.value(),
                "x_max"        : self.sb_Xmax_pol.value(),
                "x_min"        : self.sb_Xmin_pol.value(),
                "y_axis_scale" : "Linear",
                "y_max_suffix" : "",
                "y_min_suffix" : "",
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
            combo_items=["Measurement", "Math", "Expression", "Circuit Fit"]
        )

        self.hb_math = QHBoxLayout()
        self.cat1_math = QComboBox()
        self.cat1_math.addItems(["Measurement"])
        self.operator_math = QComboBox()
        self.operator_math.addItems(["+","-","x","/"])
        self.cat2_math = QComboBox()
        self.cat2_math.addItems(["Measurement"])
        self.hb_math.addWidget(self.cat1_math,3)
        self.hb_math.addWidget(self.operator_math,1)
        self.hb_math.addWidget(self.cat2_math,3)
        
        self.lcb_category = QLabelComboBox(# lcb stands for LabelComboBox
            label_text="Category",
            combo_items=["Impedance", "Reflection", "Gain", "Admittance"]
        )


        self.le_expression = QLineEdit() #le stands for LineEdit

        self.top.addWidget(self.lcb_meas)
        self.top.addWidget(self.lcb_category)
        self.top.addLayout(self.hb_math)
        self.top.addWidget(self.le_expression,3)

    # ---------- 初始化Format ---------
    def _init_fmt(self):
            # 1. 顶部固定：Format 下拉框
        self.lcb_fmt = QLabelComboBox(
            label_text="Format",
            combo_items=["Mag", "Mag(dB)", "Phase(°)", "Phase(Rad)",
                        "Tg", "Polar", "Real", "Imaginary", "Nyquist", "Nichols"]
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

        # 页 3：Polar / Nyquist / Nichols
        page_polar = QWidget()
        lay = QGridLayout(page_polar)
        self.sb_Ymax_pol = QSpinBox(); self.sb_Ymin_pol = QSpinBox()
        self.sb_Xmax_pol = QSpinBox(); self.sb_Xmin_pol = QSpinBox()
        lay.addWidget(QLabel("Ymax"),0,0); lay.addWidget(self.sb_Ymax_pol,0,1)
        lay.addWidget(QLabel("Ymin"),1,0); lay.addWidget(self.sb_Ymin_pol,1,1)
        lay.addWidget(QLabel("Xmax"),2,0); lay.addWidget(self.sb_Xmax_pol,2,1)
        lay.addWidget(QLabel("Xmin"),3,0); lay.addWidget(self.sb_Xmin_pol,3,1)
        self.fmt_stack.addWidget(page_polar)

        # 信号
        self.lcb_fmt.currentTextChanged.connect(self._on_fmt_changed)
    # ---------- 切换 Measurement ----------
    def _on_meas_changed(self):
        self._build_meas_page()

    def _build_meas_page(self):
        if self.lcb_meas.currentText() == "Measurement":
            for w in [self.cat1_math,self.cat2_math,self.operator_math,self.le_expression]:
                w.setVisible(False)
            self.lcb_category.setVisible(True)
        elif self.lcb_meas.currentText() == "Math":
            for w in [self.lcb_category, self.le_expression]:
                w.setVisible(False)
            for w in [self.cat1_math,self.cat2_math,self.operator_math]:
                w.setVisible(True)
        elif self.lcb_meas.currentText() == "Expression":
            for w in [self.lcb_category, self.cat1_math,self.cat2_math,self.operator_math]:
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
        self.cat1_math.currentTextChanged.connect(self._on_any_change)
        self.operator_math.currentTextChanged.connect(self._on_any_change)
        self.cat2_math.currentTextChanged.connect(self._on_any_change)
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

        # 第 3 页：Polar / Nyquist / Nichols
        self.sb_Ymax_pol.valueChanged.connect(self._on_any_change)
        self.sb_Ymin_pol.valueChanged.connect(self._on_any_change)
        self.sb_Xmax_pol.valueChanged.connect(self._on_any_change)
        self.sb_Xmin_pol.valueChanged.connect(self._on_any_change)
# ==================================================================
#  Demo
# ==================================================================
# ============================== 新的 DemoWindow ==============================
class DemoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TraceConfig  set_config 演示")
        self.resize(700, 350)

        self.t1 = TraceConfigWidget("Trace 1")
        self.t2 = TraceConfigWidget("Trace 2")

        # 按钮区
        self.rand_btn = QPushButton("随机配置")
        self.rand_btn.clicked.connect(self._random_config)
        self.print_btn = QPushButton("打印当前")
        self.print_btn.clicked.connect(self._print)

        lay = QVBoxLayout(self)
        lay.addWidget(self.t1)
        lay.addWidget(self.t2)
        lay.addWidget(self.rand_btn)
        lay.addWidget(self.print_btn)

        # 监听变化
        self.t1.trace_config_changed.connect(self._on_change)
        self.t2.trace_config_changed.connect(self._on_change)

    # ---------------- 随机生成字典并刷入 ----------------
    def _random_config(self):
        import random
        fmts = ["Mag", "Mag(dB)", "Phase(°)", "Phase(Rad)", "Polar", "Tg", "Real", "Imaginary", "Nyquist", "Nichols"]
        cfg = {
            "meas_type"    : random.choice(["Measurement", "Math", "Expression"]),
            "category"     : random.choice(["Impedance", "Reflection", "Gain", "Admittance"]),
            "math_cat1"    : "T1",
            "math_op"      : random.choice(["+", "-", "x", "/"]),
            "math_cat2"    : "T2",
            "expression"   : "rand()",
            "format"       : random.choice(fmts),
            "y_max"        : random.randint(10, 100),
            "y_min"        : random.randint(-100, 0),
            "x_max"        : random.randint(10, 100),
            "x_min"        : random.randint(-100, 0),
            "y_axis_scale" : random.choice(["Linear", "Log"]),
        }
        # 随机决定刷给哪个 Trace
        target = random.choice([self.t1, self.t2])
        target.set_config(cfg)

    # ---------------- 打印 ----------------
    def _print(self):
        print("----- Trace1 -----")
        print(self.t1.get_config())
        print("----- Trace2 -----")
        print(self.t2.get_config())

    # ---------------- 实时监听器 ----------------
    def _on_change(self, cfg):
        sender = self.sender().title() if hasattr(self.sender(), 'title') else 'Unknown'
        print(f"[{sender}] 配置已变动 -> {cfg}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = DemoWindow()
    w.show()
    sys.exit(app.exec_())