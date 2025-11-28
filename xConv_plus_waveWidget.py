# plot_cap_s21_real.py
import sys
from xConv.xConv import xConvS2PReader, xConvFormulaTransformer        # 读取 s2p
from custom_plot_widget.waveWidget import waveWidget        # 绘图控件
from pyqtgraph.Qt import QtWidgets

def main():
    app = QtWidgets.QApplication(sys.argv)

    # 1. 读取 s2p
    reader = xConvS2PReader("data\\GRM0115C1C100GE01_DC0V_25degC.s2p")     # 你的文件路径
    s = reader.read()                      # dict: freq, s11, s12, s21, s22, z0

    transformer = xConvFormulaTransformer()
    transformer.load_formulas(s, "xConv\\xConvFormulaDef.json")

    # 2. 计算 S21 实部
    freq = s['freq']                       # Hz
    s21_real = transformer.apply_formula(s,"abs(capZ21)")         # numpy.ndarray
    z21_abs = transformer.apply_formula(s, "imag(z21_config3)")  # 计算阻抗幅值以供参考

    # 3. 创建 waveWidget 并添加 trace
    win = waveWidget(freq_axis='log')      # 或 'lin'
    win.setWindowTitle("cap.s2p  |S21| real part")
    win.add_trace(name='S21_real',
                  x_data=freq,
                  y_data=s21_real,
                  trace_color='#00bfff',
                  unit='pF',
                  label='Capacitance (pF)')
    win.add_trace(name='Z21_abs',
                  x_data=freq,
                  y_data=z21_abs,
                  trace_color='#ff7f50',
                  unit='Ohm',
                  label='|Z21| (Ohm)')
    win.remove_trace('S21_real')  # 如果不想显示阻抗幅值，可以移除
    win.auto_range()
    win.resize(900, 600)
    win.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()