# xDrv的统一入口，从此处利用os.system调用各个子模块的驱动进行测量
# 调用命令格式: 
# python xDriver.py 
#   --device-type DEVICE_TYPE \
#   --device-tunnel  TUNNEL \
#   --device-address ADDRESS \
#   --averages AVERAGES \
#   --start-freq START_FREQ_HZ \
#   --stop-freq STOP_FREQ_HZ \
#   --sweep-type SWEEP_TYPE \
#   --sweep-points POINTS \
#   --ifbw IFBW_HZ \
#   --variable-amp VARIABLE_AMP \
#   --source-level SOURCE_LEVEL_DBM \
#   --calibration CALIBRATION_FILE \
#   --output-file OUTPUT_FILE \
import os
import argparse
import sys
def main():
    parser = argparse.ArgumentParser(description="xDriver: Unified Driver for RF Measurements")
    parser.add_argument('--device-type', type=str, required=True, help='Type of the device (e.g., VNA, Spectrum Analyzer)')
    parser.add_argument('--device-tunnel', type=str, default='USB', help='Connection tunnel type (e.g., USB, LAN)')
    parser.add_argument('--device-address', type=str, required=True, help='Device address (e.g., VISA address)')
    parser.add_argument('--averages', type=int, default=1, help='Number of averages for measurement')
    parser.add_argument('--start-freq', type=float, required=True, help='Start frequency in Hz')
    parser.add_argument('--stop-freq', type=float, required=True, help='Stop frequency in Hz')
    parser.add_argument('--sweep-type', type=str, default='LIN', help='Sweep type (LIN or LOG)')
    parser.add_argument('--sweep-points', type=int, default=201, help='Number of sweep points')
    parser.add_argument('--ifbw', type=float, default=1000.0, help='IF bandwidth in Hz')
    parser.add_argument('--variable-amp', action='store_true', help='Enable variable source amplitude')
    parser.add_argument('--source-level', type=float, default=-10.0, help='Source level in dBm')
    parser.add_argument('--calibration', type=str, help='Path to calibration file')
    parser.add_argument('--output-file', type=str, required=True, help='Path to output data file')

    args = parser.parse_args()

    # 构造调用子模块的命令
    command = f"python xDriver/{args.device_type}_driver.py "
    

if __name__ == "__main__":
    main()