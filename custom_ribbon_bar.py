import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, qApp,
                             QSplitter, QVBoxLayout, QWidget)
from PyQt5.QtCore import Qt 
from PyQt5.QtGui import QIcon, QFont

#===============Ribbon Bar===============#
from pyqtribbon import RibbonBar, RibbonButtonStyle, RibbonCategoryStyle,RibbonSpaceFindMode

#===============Custom Widget============#
from basic_custom_widget.QIconButtonWidget import QIconButtonWidget

class customRibbonBar(RibbonBar):
    def __init__(self):
        super().__init__()
        self._set_category()
        self._set_panel()

    def _set_category(self):
        self.category_home = self.addCategory("Home")
        self.category_measurement = self.addCategory("Measurement")
        self.category_view = self.addCategory("View")
        self.category_cursor = self.addCategory("Cursor")
    
    def _set_panel(self):
        self._set_category_home()
        self._set_category_measurement()
        self._set_category_view()
        self._set_category_cursor()
    
    def _set_category_home(self):
        file_panel = self.category_home.addPanel("File",showPanelOptionButton=False)
        # file_panel.setFont(QFont("Arial",5))
        self.new_button = file_panel.addSmallButton("New",QIcon("./icon/bootstrap/file-earmark-plus.svg"),alignment=Qt.AlignmentFlag.AlignLeft)
        self.open_button = file_panel.addSmallButton("Open",QIcon("./icon/bootstrap/folder2-open.svg"),alignment=Qt.AlignmentFlag.AlignLeft)
        self.export_button = file_panel.addSmallButton("Export",QIcon("./icon/bootstrap/box-arrow-right.svg"),alignment=Qt.AlignmentFlag.AlignLeft)
        self.save_button = file_panel.addSmallButton("Save",QIcon("./icon/bootstrap/save.svg"),alignment=Qt.AlignmentFlag.AlignLeft)
        self.save_as_button = file_panel.addSmallButton("Save As",QIcon("./icon/bootstrap/save-fill.svg"),alignment=Qt.AlignmentFlag.AlignLeft)
        self.report_button = file_panel.addSmallButton("Report",QIcon("./icon/bootstrap/archive.svg"),alignment=Qt.AlignmentFlag.AlignLeft)
        measurment_panel = self.category_home.addPanel("Measurement",showPanelOptionButton=False)
        measurment_panel.addLargeButton("Continuous",QIcon("./icon/bootstrap/skip-forward.svg"))
        self.single_meas_button=measurment_panel.addLargeButton("Single",QIcon("./icon/bootstrap/skip-end.svg"))
        measurment_panel.addLargeButton("Stop",QIcon("./icon/bootstrap/pause.svg"))

        plot_panel = self.category_home.addPanel("Plot",showPanelOptionButton=False)
        self.plot_large_button = plot_panel.addLargeButton("Plot",QIcon("./icon/bootstrap/graph-up-arrow.svg"))

        setup_panel = self.category_home.addPanel("Setup",showPanelOptionButton=False)
        setup_panel.addLargeButton("Transmit(Gain)",QIcon("./icon/transmission.png"))
        setup_panel.addLargeButton("Refelect(Impedance)",QIcon("./icon/reflection.png"))

        gain_calibri_panel = self.category_home.addPanel("Gain Calibration",showPanelOptionButton=False)
        gain_calibri_panel.addLargeButton("Full-Range",QIcon("./icon/gain_fullrange.png"))
        gain_calibri_panel.addLargeButton("User-Range",QIcon("./icon/gain_userrange.png"))

        impedance_calibri_panel = self.category_home.addPanel("Impedance Calibration",showPanelOptionButton=False)
        impedance_calibri_panel.addLargeButton("Full-Range",QIcon("./icon/imp_fullrange.png"))
        impedance_calibri_panel.addLargeButton("User-Range",QIcon("./icon/imp_userrange.png"))
    
    def _set_category_measurement(self):
        memory_panel = self.category_measurement.addPanel("Memory",showPanelOptionButton=False)
        memory_panel.addLargeButton("Data to Memory",QIcon("./icon/bootstrap/download.svg"),alignment=Qt.AlignmentFlag.AlignLeft)
        memory_panel.addSmallButton("Show All",QIcon("./icon/bootstrap/eye.svg"),alignment=Qt.AlignmentFlag.AlignLeft)
        memory_panel.addSmallButton("Hide All",QIcon("./icon/bootstrap/eye-slash.svg"),alignment=Qt.AlignmentFlag.AlignLeft)
        memory_panel.addSmallButton("Delete All",QIcon("./icon/bootstrap/trash.svg"),alignment=Qt.AlignmentFlag.AlignLeft)
        
        traces_panel = self.category_measurement.addPanel("Traces",showPanelOptionButton=False)
        traces_panel.addLargeButton("Add Trace",QIcon("./icon/add_trace.png"))
        traces_panel.addLargeButton("Add Math",QIcon("./icon/bootstrap/plus-slash-minus.svg"))
        traces_panel.addLargeButton("Add Expression",QIcon("./icon/bootstrap/calculator.svg"))
        traces_panel.addLargeButton("Add Circuit Fit",QIcon("./icon/circuit_fit.png"))
        stability_analysis_panel = self.category_measurement.addPanel("Stability Analysis",showPanelOptionButton=False)
        stability_analysis_panel.addLabel("Instability Point:")
        stability_analysis_panel.addMediumComboBox(["    +1    ","    -1    "])

    def _set_category_view(self):
        chart_setup_panel = self.category_view.addPanel("Trace Setup",showPanelOptionButton=False)
        chart_setup_panel.addLabel("Plot")
        chart_setup_panel.addSmallButton("Group",QIcon("./icon/bootstrap/collection.svg"),alignment=Qt.AlignmentFlag.AlignLeft)
        chart_setup_panel.addSmallButton("Split",QIcon("./icon/bootstrap/layout-split.svg"),alignment=Qt.AlignmentFlag.AlignLeft)
        chart_setup_panel.addLabel("Arrange")
        chart_setup_panel.addSmallButton("Horizon",QIcon("./icon/bootstrap/distribute-vertical.svg"),alignment=Qt.AlignmentFlag.AlignLeft)
        chart_setup_panel.addSmallButton("Vertical",QIcon("./icon/bootstrap/distribute-horizontal.svg"),alignment=Qt.AlignmentFlag.AlignLeft)
        # chart_setup_panel.addComboBox(["Auto Axis Placement","One Axis Per Chart"])
        # chart_setup_panel.addComboBox(["Arrange Horizontally","Arrange Vertically"])
        average_panel = self.category_view.addPanel("Average")
        average_panel.addLargeButton("Avg Meas",QIcon("./icon/average.png"))
        average_panel.addLabel("Average Factor:")
        # average_panel.addSmallVerticalSeparator()
        average_panel.addSpinBox()

        annotation_panel = self.category_view.addPanel("Annotations",showPanelOptionButton=False)
        annotation_panel.addLargeButton("Text Note",QIcon("./icon/bootstrap/card-heading.svg"))

    def _set_category_cursor(self):
        cursors_panel = self.category_cursor.addPanel("Cursors",showPanelOptionButton=False)
        cursors_panel.addLargeButton("Add Cursor",QIcon("./icon/bootstrap/cursor-text.svg"))
        cursors_panel.addLargeButton("Add Delta Cursor",QIcon("./icon/bootstrap/input-cursor-text.svg"))

        cursor_calculation_panel = self.category_cursor.addPanel("Cursor Calculation",showPanelOptionButton=False)
        cursor_calculation_panel.addComboBox(["None","Basic Phase Margin Calculation","Advanced Phase Margin Calculation", "Resonance Frequency - Quality Calculation","Stability Margin Calculation"])

        linked_cursors_panel = self.category_cursor.addPanel("Linked Cursors",showPanelOptionButton=False)
        
        linked_cursors_panel.addLargeButton("Link Cursors",QIcon("./icon/bootstrap/link-45deg.svg"))
        linked_cursors_panel.addVerticalSeparator()
        linked_cursors_panel.addLabel("Cursor Distance:")
        linked_cursors_panel.addComboBox(["Decade(10)","Octave(2)","Linear"])
        linked_cursors_panel.addLabel(" ")

        linked_cursors_panel.addVerticalSeparator()
        linked_cursors_panel.addLabel("Cursor A")
        linked_cursors_panel.addComboBox(["Cursor 1","Cursor 2","Cursor 3"])
        linked_cursors_panel.addLabel(" ")

        linked_cursors_panel.addVerticalSeparator()
        linked_cursors_panel.addLabel("Cursor B:")
        linked_cursors_panel.addComboBox(["Cursor 1","Cursor 2","Cursor 3"])
        