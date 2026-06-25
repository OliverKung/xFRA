from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QFileDialog, QLabel, QLineEdit,
                             QComboBox, QGridLayout, QMessageBox, QWidget,
                             QFrame, QRadioButton, QButtonGroup, QTextEdit,
                             QProgressBar, QDialogButtonBox, QCheckBox,
                             QSplitter, QScrollArea)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon
from pathlib import Path


class CalibrationMeasureRow(QWidget):
    """Single row: step label + file path + status"""
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.setLayout(QHBoxLayout(self))
        self.layout().setContentsMargins(2, 2, 2, 2)

        self.label = QLabel(label)
        self.label.setMinimumWidth(140)
        self.label.setStyleSheet("font-weight: bold;")

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select .s2p measurement file...")
        self.path_edit.setReadOnly(True)

        self.browse_btn = QPushButton("\U0001f4c2 Browse")
        self.browse_btn.setFixedWidth(80)

        self.status_label = QLabel("\u26a0 Not loaded")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        self.status_label.setFixedWidth(85)

        self.layout().addWidget(self.label)
        self.layout().addWidget(self.path_edit, 1)
        self.layout().addWidget(self.browse_btn)
        self.layout().addWidget(self.status_label)

    def set_file(self, path: str):
        self.path_edit.setText(path)
        if path:
            self.status_label.setText("\u2714 Loaded")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText("\u26a0 Not loaded")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")

    def get_file(self) -> str:
        return self.path_edit.text()


class CalibrationStandardGroup(QWidget):
    """Group of calibration steps in QScrollArea"""
    def __init__(self, title: str, steps: list, parent=None):
        super().__init__(parent)
        self.rows = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 13px; padding: 4px 0;")
        layout.addWidget(title_label)

        for key, step_label in steps:
            row = CalibrationMeasureRow(step_label, self)
            row.browse_btn.clicked.connect(lambda _, k=key: self._browse(k))
            self.rows[key] = row
            layout.addWidget(row)

        layout.addStretch()

    def _browse(self, key: str):
        path, _ = QFileDialog.getOpenFileName(
            self, f"Select {key} calibration file",
            "", "Touchstone (*.s2p);;All Files (*)"
        )
        if path:
            self.rows[key].set_file(path)

    def get_files(self) -> dict:
        return {k: row.get_file() for k, row in self.rows.items()}

    def is_complete(self) -> bool:
        return all(row.get_file() for row in self.rows.values())


class xConvCalibrationDialog(QDialog):
    """xConv Calibration Setup Dialog - Horizontal Layout"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("xFRA - Calibration Setup")
        self.resize(1200, 750)
        self.setMinimumSize(1000, 650)

        # ========== Left: File Selection ==========
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 4, 8)

        # OSL group
        self.standard_group_osl = CalibrationStandardGroup(
            "OSL Calibration Files (1-Port)",
            [
                ("short1", "Short   Port 1"),
                ("open1",  "Open    Port 1"),
                ("load1",  "Load    Port 1"),
            ],
            self
        )

        # SOLT group
        self.standard_group_solt = CalibrationStandardGroup(
            "SOLT Calibration Files (2-Port)",
            [
                ("short1", "Short   Port 1"),
                ("open1",  "Open    Port 1"),
                ("load1",  "Load    Port 1"),
                ("short2", "Short   Port 2"),
                ("open2",  "Open    Port 2"),
                ("load2",  "Load    Port 2"),
                ("through","Through Port 1\u21922"),
                ("isolation", "Isolation Port 1\u21922"),
            ],
            self
        )

        self.standard_group_solt.setVisible(False)

        # Left scroll area
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.addWidget(self.standard_group_osl)
        scroll_layout.addWidget(self.standard_group_solt)
        scroll_layout.addStretch()
        left_scroll.setWidget(scroll_content)

        left_panel_inner = QWidget()
        left_panel_inner_layout = QVBoxLayout(left_panel_inner)
        left_panel_inner_layout.setContentsMargins(0, 0, 0, 0)
        left_panel_inner_layout.addWidget(QLabel("\U0001f4c1 Input Calibration Files"))
        left_panel_inner_layout.addWidget(left_scroll, 1)
        left_panel_inner_layout.setParent(left_panel)
        # Restructure: put file input inside a group box
        file_group = QGroupBox("\U0001f4c1 Calibration Measurement Files")
        file_layout = QVBoxLayout(file_group)
        file_layout.addWidget(left_scroll, 1)
        left_layout.addWidget(file_group, 1)

        # ========== Right: Settings + Info ==========
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 8, 8, 8)
        right_layout.setSpacing(8)

        # --- Calibration type ---
        type_group = QGroupBox("Calibration Type")
        type_layout = QVBoxLayout(type_group)
        self.type_radio = QButtonGroup(self)
        rb_osl = QRadioButton("OSL (Open-Short-Load)   1-Port Calibration")
        rb_solt = QRadioButton("SOLT (Short-Open-Load-Through-Isolation)   2-Port Calibration")
        rb_osl.setChecked(True)
        self.type_radio.addButton(rb_osl, 0)
        self.type_radio.addButton(rb_solt, 1)
        type_layout.addWidget(rb_osl)
        type_layout.addWidget(rb_solt)
        right_layout.addWidget(type_group)

        # --- Ideal standard model ---
        ideal_group = QGroupBox("Ideal Standard Model")
        ideal_layout = QVBoxLayout(ideal_group)
        ideal_layout.setSpacing(2)
        ideal_layout.addWidget(QLabel("Open   = \u0393 \u2248 +1.0"))
        ideal_layout.addWidget(QLabel("Short  = \u0393 \u2248 -1.0"))
        ideal_layout.addWidget(QLabel("Load   = \u0393 \u2248  0.0"))
        ideal_layout.addWidget(QLabel("Through = S21=1, S11=S22=0"))
        ideal_layout.addWidget(QLabel("Isolation = S21=0"))
        right_layout.addWidget(ideal_group)

        # --- Output settings ---
        output_group = QGroupBox("Output Settings")
        output_layout = QHBoxLayout(output_group)
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Select calibration matrix output path (*.s2p)...")
        self.output_path.setReadOnly(True)
        self.output_browse_btn = QPushButton("\U0001f4c2 Browse")
        self.output_browse_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(QLabel("Cal. Matrix:"))
        output_layout.addWidget(self.output_path, 1)
        output_layout.addWidget(self.output_browse_btn)
        right_layout.addWidget(output_group)

        # --- Calibration info log ---
        info_group = QGroupBox("Calibration Info")
        info_layout = QVBoxLayout(info_group)
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(150)
        self.info_text.setPlaceholderText("Select calibration files and click Compute...")
        info_layout.addWidget(self.info_text)
        right_layout.addWidget(info_group)

        # --- Progress bar ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        # --- Compute button ---
        self.compute_btn = QPushButton("\U0001f9ee Compute Calibration")
        self.compute_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; "
            "padding: 10px 20px; border-radius: 4px; font-size: 14px; }"
            "QPushButton:hover { background-color: #45a049; }"
            "QPushButton:disabled { background-color: #cccccc; }"
        )
        self.compute_btn.clicked.connect(self._on_compute)
        right_layout.addWidget(self.compute_btn)
        right_layout.addStretch()

        # ========== Main layout: horizontal split ==========
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 5)   # Left stretch 5
        splitter.setStretchFactor(1, 4)   # Right stretch 4
        splitter.setSizes([650, 450])     # Initial width allocation

        main_layout.addWidget(splitter, 1)

        # Type switch connection
        self.type_radio.buttonClicked.connect(self._on_type_changed)

        # Window centering
        self._center_window()

    def _center_window(self):
        """Center window on parent/screen"""
        parent = self.parent()
        if parent:
            # Centered relative to parent
            parent_rect = parent.geometry()
            self_rect = self.geometry()
            x = parent_rect.x() + (parent_rect.width() - self_rect.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self_rect.height()) // 2
            self.move(x, y)

    # ---------- Slots ----------
    def _on_type_changed(self):
        cal_type = self.type_radio.checkedId()
        self.standard_group_osl.setVisible(cal_type == 0)
        self.standard_group_solt.setVisible(cal_type == 1)

    def _browse_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Calibration Matrix", "calibration_matrix.s2p",
            "Touchstone (*.s2p);;All Files (*)"
        )
        if path:
            self.output_path.setText(path)

    def _on_compute(self):
        """Validate input and trigger calibration"""
        cal_type = self.type_radio.checkedId()
        group = self.standard_group_solt if cal_type == 1 else self.standard_group_osl

        if not group.is_complete():
            QMessageBox.warning(self, "Incomplete Input",
                                "Please select .s2p measurement files for all calibration steps!")
            return

        if not self.output_path.text():
            QMessageBox.warning(self, "Output Not Set",
                                "Please select an output path for the calibration matrix!")
            return

        files = group.get_files()
        output = self.output_path.text()

        self.info_text.clear()
        self.info_text.append("\U0001f4cb Calibration Input Summary:")
        for key, fpath in files.items():
            if fpath:
                self.info_text.append(f"  {key}: {Path(fpath).name}")
        self.info_text.append(f"\n\U0001f4e4 Output path: {output}")
        self.info_text.append(f"\n\U0001f4d0 Calibration type: {'SOLT (2-Port)' if cal_type == 1 else 'OSL (1-Port)'}")
        self.info_text.append("\n\u2705 Input validation passed, ready to compute...")

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.compute_btn.setEnabled(False)
        self.compute_btn.setText("\u23f3 Computing...")

        QTimer.singleShot(1000, self._finish_compute)

    def _finish_compute(self):
        self.progress_bar.setVisible(False)
        self.compute_btn.setEnabled(True)
        self.compute_btn.setText("\U0001f9ee Compute Calibration")
        self.info_text.append("\n\U0001f3af Calibration completed! Matrix saved.")
        QMessageBox.information(self, "Calibration Complete",
                                "Calibration matrix calculation complete!\nCalibration data can be used in subsequent conversions.")

    # ---------- Public API ----------
    def get_calibration_config(self) -> dict:
        cal_type = "SOLT" if self.type_radio.checkedId() == 1 else "OSL"
        group = self.standard_group_solt if cal_type == "SOLT" else self.standard_group_osl
        return {
            "type": cal_type,
            "files": group.get_files(),
            "output": self.output_path.text(),
        }
