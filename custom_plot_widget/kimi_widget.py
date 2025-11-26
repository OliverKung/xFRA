import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets


class PlotWidget(QtWidgets.QWidget):
    """
    单窗口多迹线绘图Widget，支持双Y轴和光标值显示
    
    特性：
    - 支持显示多条迹线，每条可指定左/右Y轴
    - 右上角实时显示光标处各迹线的值
    - Ctrl+鼠标移动进入自由光标模式（不吸附数据点）
    - 提供完整的迹线增删改接口和轴配置接口
    """
    cursorMoved = QtCore.Signal(float, dict)  # x_value, {trace_name: y_value}

    def __init__(self, parent=None, x_axis_type='log'):
        super().__init__(parent)
        self.traces = {}  # name -> trace_info dict
        self.x_axis_type = x_axis_type.lower()
        self._x_range_set = False  # 标记X轴范围是否已初始化
        
        # 主布局
        self.lay = QtWidgets.QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(0)
        
        # 绘图控件
        self.plot_widget = pg.PlotWidget()
        self.lay.addWidget(self.plot_widget)
        
        # 初始化坐标轴
        self._setup_axes()
        
        # 光标元素
        self.vLine = pg.InfiniteLine(angle=90, movable=False, 
                                     pen=pg.mkPen('#ffeb3b', width=1.2))
        self.plot_widget.addItem(self.vLine)
        self.hLines = {}  # trace_name -> InfiniteLine
        
        # 光标值标签（右上角）
        self.cursor_label = pg.TextItem(
            anchor=(1, 0), color='#ffeb3b', 
            border=pg.mkPen('#ffeb3b', width=0.5),
            fill=pg.mkBrush('#161616')
        )
        self.plot_widget.addItem(self.cursor_label)
        
        # 鼠标事件代理
        self.proxy = pg.SignalProxy(
            self.plot_widget.scene().sigMouseMoved,
            rateLimit=60, slot=self._mouse_moved
        )
        
        # 连接视图范围变化信号
        self.plot_widget.plotItem.vb.sigRangeChanged.connect(
            self._update_cursor_label_position
        )

    # ==================== 核心修复 ====================
    def _setup_axes(self):
        """初始化坐标轴样式和配置"""
        # 背景
        self.plot_widget.setBackground('#161616')
        
        # 底轴
        bottom = self.plot_widget.getAxis('bottom')
        bottom.setPen(pg.mkPen('#999', width=0.5))
        self.plot_widget.setLabel('bottom', 'Frequency (Hz)')
        
        # 左轴
        left = self.plot_widget.getAxis('left')
        left.setPen(pg.mkPen('#999', width=0.5))
        self.plot_widget.setLabel('left', 'Magnitude')
        
        # 右轴（初始隐藏）
        self.plot_widget.showAxis('right', False)
        right = self.plot_widget.getAxis('right')
        right.setPen(pg.mkPen('#999', width=0.5))
        right.setLabel('')
        
        # 网格
        self.plot_widget.showGrid(x=True, y=True, alpha=60)
        
        # 对数/线性模式
        if self.x_axis_type == 'log':
            self.plot_widget.setLogMode(x=True, y=False)
        else:
            self.plot_widget.setLogMode(x=False, y=False)
            
        # 鼠标交互（禁用Y轴拖动）
        self.plot_widget.getViewBox().setMouseEnabled(x=True, y=False)
        
        # ===== 创建右轴ViewBox =====
        self.right_viewbox = pg.ViewBox()
        self.plot_widget.scene().addItem(self.right_viewbox)
        self.plot_widget.getAxis('right').linkToView(self.right_viewbox)
        
        # 关键1：链接X轴，但禁用X轴自动缩放（由主ViewBox控制）
        self.right_viewbox.setXLink(self.plot_widget.plotItem)
        self.right_viewbox.enableAutoRange(axis='x', enable=False)
        
        # 关键2：启用Y轴自动缩放
        self.right_viewbox.enableAutoRange(axis='y', enable=True)
        
        # 关键3：同步X轴范围变化
        self.plot_widget.plotItem.vb.sigXRangeChanged.connect(
            self._update_right_axis_xrange
        )

    def _update_right_axis_xrange(self):
        """同步右轴ViewBox的X轴范围到主ViewBox"""
        x_range = self.plot_widget.plotItem.vb.viewRange()[0]
        self.right_viewbox.setXRange(*x_range, padding=0)
    # ==================================================

    def add_trace(self, name, x_data, y_data, axis='left', color=None, 
                  unit='', label=None):
        """
        添加迹线
        
        Parameters
        ----------
        name : str
            迹线唯一标识符
        x_data, y_data : array-like
            数据数组
        axis : {'left', 'right'}, optional
            指定使用左/右Y轴
        color : str, optional
            颜色代码（如'#00d2ff'）
        unit : str, optional
            单位字符串（如'dB'、'°'）
        label : str, optional
            显示标签（默认同name）
        """
        if name in self.traces:
            raise ValueError(f"Trace '{name}' already exists")
        
        # 自动分配颜色
        if color is None:
            palette = ['#00d2ff', '#ff8c00', '#00ff88', '#ff44ff', '#ffff44']
            color = palette[len(self.traces) % len(palette)]
        
        # 创建曲线
        pen = pg.mkPen(color, width=1.8)
        if axis == 'right':
            curve = pg.PlotCurveItem(pen=pen)
            self.right_viewbox.addItem(curve)
            self.plot_widget.showAxis('right', True)
        else:
            curve = self.plot_widget.plot(pen=pen)
            axis = 'left'
        
        # 创建水平光标线（初始隐藏）
        hLine = pg.InfiniteLine(
            angle=0, movable=False,
            pen=pg.mkPen(color, width=1.0, style=QtCore.Qt.DashLine)
        )
        self.plot_widget.addItem(hLine)
        hLine.hide()
        self.hLines[name] = hLine
        
        # 存储迹线信息
        self.traces[name] = {
            'curve': curve,
            'axis': axis,
            'color': color,
            'unit': unit,
            'label': label or name,
            'data_x': np.asarray(x_data, dtype=float),
            'data_y': np.asarray(y_data, dtype=float)
        }
        
        self._update_trace_curve(name)
        self._auto_scale_axes()
        
    def remove_trace(self, name):
        """删除指定迹线"""
        if name not in self.traces:
            return
        
        trace = self.traces[name]
        if trace['axis'] == 'right':
            self.right_viewbox.removeItem(trace['curve'])
        else:
            self.plot_widget.removeItem(trace['curve'])
        
        self.plot_widget.removeItem(self.hLines[name])
        del self.hLines[name]
        del self.traces[name]
        
        # 无右轴迹线时隐藏右轴
        if not any(t['axis'] == 'right' for t in self.traces.values()):
            self.plot_widget.showAxis('right', False)

    def clear_traces(self):
        """清空所有迹线"""
        for name in list(self.traces.keys()):
            self.remove_trace(name)
            
    def update_trace(self, name, x_data=None, y_data=None):
        """
        更新迹线数据
        
        Parameters
        ----------
        name : str
            迹线名称
        x_data, y_data : array-like, optional
            新数据（None则保持原数据）
        """
        if name not in self.traces:
            raise ValueError(f"Trace '{name}' does not exist")
        
        trace = self.traces[name]
        if x_data is not None:
            trace['data_x'] = np.asarray(x_data, dtype=float)
        if y_data is not None:
            trace['data_y'] = np.asarray(y_data, dtype=float)
        
        self._update_trace_curve(name)
        self._auto_scale_axes()
        
    def _update_trace_curve(self, name):
        """更新曲线显示数据"""
        trace = self.traces[name]
        x = trace['data_x']
        y = trace['data_y']
        
        # X轴变换（对数/线性）
        if self.x_axis_type == 'log':
            # 确保数据为正
            if np.any(x <= 0):
                print(f"警告：迹线 '{name}' 的X轴数据包含非正值，对数坐标无法显示")
                x_disp = np.log10(np.maximum(x, 1e-6))
            else:
                x_disp = np.log10(x)
        else:
            x_disp = x
            
        trace['curve'].setData(x_disp, y)
        
    def set_axis_properties(self, axis, label=None, range=None):
        """
        配置坐标轴属性
        
        Parameters
        ----------
        axis : {'left', 'right'}
            目标轴
        label : str, optional
            轴标签文本
        range : tuple, optional
            (min, max)范围
        """
        if axis == 'left':
            ax_obj = self.plot_widget.getAxis('left')
            vb = self.plot_widget.getViewBox()
        elif axis == 'right':
            ax_obj = self.plot_widget.getAxis('right')
            vb = self.right_viewbox
        else:
            raise ValueError("axis must be 'left' or 'right'")
        
        if label is not None:
            ax_obj.setLabel(label)
        
        if range is not None:
            vb.setYRange(*range)
            
    def set_x_axis_properties(self, label=None, range=None):
        """配置X轴属性"""
        if label is not None:
            self.plot_widget.setLabel('bottom', label)
        
        if range is not None:
            if self.x_axis_type == 'log':
                self.plot_widget.setXRange(np.log10(range[0]), np.log10(range[1]), padding=0)
            else:
                self.plot_widget.setXRange(*range, padding=0)
        
    def _mouse_moved(self, evt):
        """鼠标移动事件处理"""
        pos = evt[0]
        if not self.plot_widget.sceneBoundingRect().contains(pos):
            return
        
        mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
        x_view = mouse_point.x()
        
        # 检查Ctrl键（自由模式）
        ctrl = (pg.QtGui.QGuiApplication.keyboardModifiers() == 
                QtCore.Qt.ControlModifier)
        
        # 更新垂直线
        self.vLine.setPos(x_view)
        
        if not self.traces:
            self.cursor_label.setText(f"X: {x_view:.6g}")
            return
        
        # 以第一条迹线的X数据为基准
        ref_x = next(iter(self.traces.values()))['data_x']
        
        if ctrl:
            # 自由模式
            cursor_text = f"X: {x_view:.6g}"
            y_values = {}
            
            for name, trace in self.traces.items():
                self.hLines[name].hide()
                
                # 插值获取近似值（取最近点）
                if self.x_axis_type == 'log':
                    idx = np.argmin(np.abs(np.log10(ref_x) - x_view))
                else:
                    idx = np.argmin(np.abs(ref_x - x_view))
                
                if idx < len(trace['data_y']):
                    y_val = trace['data_y'][idx]
                    y_values[name] = y_val
                    cursor_text += f"\n{trace['label']}: {y_val:.3f} {trace['unit']}"
            
            self.cursorMoved.emit(x_view, y_values)
        else:
            # 吸附到最近数据点
            if self.x_axis_type == 'log':
                idx = int(np.argmin(np.abs(np.log10(ref_x) - x_view)))
            else:
                idx = int(np.argmin(np.abs(ref_x - x_view)))
            
            x_val = ref_x[idx]
            x_display = np.log10(x_val) if self.x_axis_type == 'log' else x_val
            
            cursor_text = f"X: {x_val:.6g}"
            y_values = {}
            
            # 更新所有迹线的水平线
            for name, trace in self.traces.items():
                if idx < len(trace['data_y']):
                    y_val = trace['data_y'][idx]
                    y_values[name] = y_val
                    self.hLines[name].setPos(y_val)
                    self.hLines[name].show()
                    cursor_text += f"\n{trace['label']}: {y_val:.3f} {trace['unit']}"
            
            # 垂直线吸附到数据点
            self.vLine.setPos(x_display)
            self.cursorMoved.emit(x_val, y_values)
        
        self.cursor_label.setText(cursor_text)
        
    def _update_cursor_label_position(self):
        """保持光标标签在右上角"""
        view_range = self.plot_widget.viewRange()
        if view_range is None:
            return
        
        x_max, y_max = view_range[0][1], view_range[1][1]
        x_margin = (view_range[0][1] - view_range[0][0]) * 0.02
        y_margin = (view_range[1][1] - view_range[1][0]) * 0.02
        
        self.cursor_label.setPos(x_max - x_margin, y_max - y_margin)
        
    def _auto_scale_axes(self):
        """自动缩放Y轴（关键修复）"""
        left_data, right_data = [], []
        
        # 收集数据
        for trace in self.traces.values():
            if len(trace['data_y']) > 0:
                if trace['axis'] == 'left':
                    left_data.extend(trace['data_y'])
                else:
                    right_data.extend(trace['data_y'])
        
        # 左轴范围
        if left_data:
            y_min, y_max = np.min(left_data), np.max(left_data)
            margin = max((y_max - y_min) * 0.1, 1e-6)
            self.plot_widget.getViewBox().setYRange(y_min - margin, y_max + margin)
        
        # 右轴范围
        if right_data:
            y_min, y_max = np.min(right_data), np.max(right_data)
            margin = max((y_max - y_min) * 0.1, 1e-6)
            self.right_viewbox.setYRange(y_min - margin, y_max + margin)
        
        # ===== 修复：仅在首次添加迹线时设置X轴范围 =====
        if not self._x_range_set and self.traces:
            all_x = np.concatenate([t['data_x'] for t in self.traces.values()])
            if len(all_x) > 0:
                x_min, x_max = np.min(all_x), np.max(all_x)
                
                # 对数坐标下确保x_min>0
                if self.x_axis_type == 'log' and x_min <= 0:
                    x_min = max(x_min, 1e-12) if x_max > 0 else 1e-6
                
                if self.x_axis_type == 'log':
                    self.plot_widget.setXRange(np.log10(x_min), np.log10(x_max), padding=0)
                else:
                    self.plot_widget.setXRange(x_min, x_max, padding=0)
                
                self._x_range_set = True


# 使用示例
if __name__ == '__main__':
    import sys
    
    app = QtWidgets.QApplication(sys.argv)
    
    # 创建Widget
    pw = PlotWidget(x_axis_type='log')
    pw.setWindowTitle("多迹线绘图Widget示例")
    pw.resize(800, 600)
    
    # 生成示例数据
    freq = np.logspace(6, 9, 500)  # 1MHz-1GHz
    
    # 添加S21幅度迹线（左轴）
    s21_mag = -20 * np.log10(freq/1e9) + np.random.randn(500)*0.5
    pw.add_trace(
        'S21_mag', freq, s21_mag, 
        axis='left', color='#00d2ff', unit='dB', label='|S21|'
    )
    
    # 添加S21相位迹线（右轴）
    s21_phase = np.unwrap(np.angle(freq/1e9 * np.pi)) * 180/np.pi
    pw.add_trace(
        'S21_phase', freq, s21_phase,
        axis='right', color='#ff8c00', unit='°', label='∠S21'
    )
    
    # 配置坐标轴
    pw.set_axis_properties('left', label='Magnitude (dB)')
    pw.set_axis_properties('right', label='Phase (°)')
    
    # 连接光标信号
    def on_cursor(freq, values):
        print(f"光标频率: {freq:.3e} Hz, 值: {values}")
    
    pw.cursorMoved.connect(on_cursor)
    
    pw.show()
    sys.exit(app.exec())