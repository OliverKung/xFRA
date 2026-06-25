import sys

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    # UI labels
    ("校准设置对话框", "Calibration Setup Dialog"),
    ("左侧面板：文件选择区", "Left: File Selection"),
    ("右侧面板：设置 + 信息", "Right: Settings + Info"),
    # GroupBox titles
    ("校准测量文件 Calibration Measurement Files", "Calibration Measurement Files"),
    ("校准类型 Calibration Type", "Calibration Type"),
    ("理想标准件模型 Ideal Standard Model", "Ideal Standard Model"),
    ("输出设置 Output Settings", "Output Settings"),
    ("校准信息 Calibration Info", "Calibration Info"),
    # Radio buttons
    ("OSL (Open-Short-Load)   单端口校准", "OSL (Open-Short-Load)   1-Port Calibration"),
    ("SOLT (Short-Open-Load-Through-Isolation)   双端口校准", "SOLT (Short-Open-Load-Through-Isolation)   2-Port Calibration"),
    # Ideal model labels
    ("Open   = Γ ≈ +1.0  (开路反射)", "Open   = Γ ≈ +1.0"),
    ("Short  = Γ ≈ -1.0  (短路反射)", "Short  = Γ ≈ -1.0"),
    ("Load   = Γ ≈  0.0  (匹配负载)", "Load   = Γ ≈  0.0"),
    ("Through = S21=1, S11=S22=0 (理想直通)", "Through = S21=1, S11=S22=0"),
    ("Isolation = S21=0 (理想隔离)", "Isolation = S21=0"),
    # Output settings
    ("校准矩阵:", "Cal. Matrix:"),
    ("选择校准矩阵输出路径 (*.s2p)...", "Select calibration matrix output path (*.s2p)..."),
    ("选择路径", "Browse"),
    # Info text placeholder
    ("选择校准文件后点击下方按钮进行计算...", "Select calibration files and click Compute..."),
    # Buttons
    ("计算校准 Compute Calibration", "Compute Calibration"),
    ("计算中...", "Computing..."),
    ("计算校准", "Compute Calibration"),
    # CalibrationStandardGroup titles
    ("OSL 校准文件 (单端口)", "OSL Calibration Files (1-Port)"),
    ("SOLT 校准文件 (双端口)", "SOLT Calibration Files (2-Port)"),
    # Step labels
    ("Short (短路)   Port 1", "Short   Port 1"),
    ("Open (开路)    Port 1", "Open    Port 1"),
    ("Load (负载)    Port 1", "Load    Port 1"),
    ("Short (短路)   Port 2", "Short   Port 2"),
    ("Open (开路)    Port 2", "Open    Port 2"),
    ("Load (负载)    Port 2", "Load    Port 2"),
    ("Through (直通)  Port 1→2", "Through Port 1→2"),
    ("Isolation (隔离) Port 1→2", "Isolation Port 1→2"),
    # Row status
    ("未加载", "Not loaded"),
    ("已加载", "Loaded"),
    # Browse button
    ("浏览", "Browse"),
    ("选择 .s2p 测量文件...", "Select .s2p measurement file..."),
    # Window title
    ("xFRA - 校准设置 Calibration Setup", "xFRA - Calibration Setup"),
    # Log messages
    ("校准输入摘要:", "Calibration Input Summary:"),
    ("输出路径:", "Output path:"),
    ("校准类型:", "Calibration type:"),
    ("SOLT (双端口)", "SOLT (2-Port)"),
    ("OSL (单端口)", "OSL (1-Port)"),
    ("输入校验通过，准备计算...", "Input validation passed, ready to compute..."),
    ("校准计算完成！校准矩阵已保存。", "Calibration completed! Matrix saved."),
    ("校准完成", "Calibration Complete"),
    ("可在后续转换中使用校准数据。", "Calibration data can be used in subsequent conversions."),
    ("校准矩阵计算完成！", "Calibration matrix calculation complete!"),
    ("请先为所有校准步骤选择对应的", "Please select measurement files for all calibration steps"),
    # Messages
    ("输入不完整", "Incomplete Input"),
    ("输出未设置", "Output Not Set"),
    ("请选择校准矩阵的输出路径！", "Please select an output path for the calibration matrix!"),
    ("的", ""),
    # Placeholder
    ("选择校准文件", "Select calibration file"),
    # File dialog
    ("Touchstone 文件 (*.s2p);;所有文件 (*)", "Touchstone (*.s2p);;All Files (*)"),
    ("保存校准矩阵", "Save Calibration Matrix"),
    ("选择 {0} 校准测量文件", "Select {0} calibration measurement file"),
    # Window centering
    ("让窗口在父窗口（或屏幕）中居中", "Center window on parent/screen"),
    ("相对于父窗口居中", "Centered relative to parent"),
    # Class comments
    ("xConv 校准设置对话框 - 横向布局", "xConv Calibration Setup Dialog - Horizontal Layout"),
    ("单行：校准步骤标签 + 文件路径选择 + 状态", "Single row: step label + file path + status"),
    ("一组校准步骤（如 OSL 的 3 个标准），放在 QScrollArea 中", "Group of calibration steps in QScrollArea"),
    # Layout comments
    ("左侧面板：文件选择区", "Left panel: file selection"),
    ("右侧面板：设置 + 信息", "Right panel: settings + info"),
    ("主布局：左右分割", "Main layout: horizontal split"),
    ("左侧占 5", "Left stretch 5"),
    ("右侧占 4", "Right stretch 4"),
    ("初始宽度分配", "Initial width allocation"),
    ("连接类型切换", "Type switch connection"),
    ("窗口居中", "Window centering"),
    ("校准设置", "Calibration Setup"),
    ("校准完成", "Calibration Complete"),
    ("计算按钮", "Compute button"),
    ("槽函数", "Slots"),
    ("公共接口", "Public API"),
    ("进度条", "Progress bar"),
    ("输入校验并触发校准计算", "Validate input and trigger calibration"),
    ("让窗口在父窗口", "Center window relative to parent"),
]

for old, new in replacements:
    content = content.replace(old, new)

with open(sys.argv[1], 'w', encoding='utf-8') as f:
    f.write(content)
print('Replaced all Chinese')