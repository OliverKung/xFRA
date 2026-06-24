# xDrviver/VNA_Class/SVA1000X_Emu.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# xDrvSetting begin
# device-type VNA
# model SVA1000X_Emu
# tunnel visa socket
# average yes
# min-freq 100
# max-freq 5000000000
# sweep-type LOG LIN
# sweep-points 101 10001
# ifbw 10000
# variable-amp no
# source-level -20 0
# level-unit dBm
# Receiver1Attn 0
# Receiver2Attn 0
# xDrvSetting end
# Usage examples:
#   VISA:   python SVA1000X_Emu.py --device-tunnel VISA   --device-address TCPIP0::192.168.1.100::INSTR ...
#   SOCKET: python SVA1000X_Emu.py --device-tunnel SOCKET --device-address 127.0.0.1 --device-port 5025 ...

import argparse
import sys
import time
import socket

# pyvisa is imported lazily inside main() only for VISA tunnel


class SocketSCPI:
    """Raw socket SCPI client that mimics pyvisa Resource interface.

    Provides write(), query(), read(), query_ascii_values(), close()
    and a timeout attribute so existing driver functions work unchanged.
    """

    def __init__(self, host, port=5025, timeout=20000):
        self._host = host
        self._port = port
        self._timeout = timeout / 1000.0  # convert ms to seconds
        self._sock = socket.create_connection((host, port), timeout=self._timeout)
        # Drain welcome banner if any (non-blocking)
        self._sock.settimeout(0.3)
        try:
            self._sock.recv(4096)
        except socket.timeout:
            pass
        self._sock.settimeout(self._timeout)

    @property
    def timeout(self):
        return int(self._timeout * 1000)

    @timeout.setter
    def timeout(self, ms):
        self._timeout = ms / 1000.0
        self._sock.settimeout(self._timeout)

    def write(self, cmd):
        """Send a SCPI command (\\n appended automatically)."""
        payload = (cmd.rstrip() + "\n").encode()
        self._sock.sendall(payload)

    def read(self):
        """Read response until the connection idles."""
        self._sock.settimeout(0.5)
        data = b""
        while True:
            try:
                chunk = self._sock.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(chunk) < 4096:
                    break
            except socket.timeout:
                break
        self._sock.settimeout(self._timeout)
        return data.decode().strip()

    def query(self, cmd):
        """Send a query and return the response string."""
        self.write(cmd)
        return self.read()

    def query_ascii_values(self, cmd):
        """Send a query and return parsed float list.

        Handles both comma-separated and whitespace-separated responses.
        """
        raw = self.query(cmd)
        parts = raw.replace(",", " ").split()
        return [float(p) for p in parts]

    def close(self):
        try:
            self._sock.close()
        except Exception:
            pass


def parse_arguments():
    parser = argparse.ArgumentParser(description="Siglent VNA S2P Measurement Driver")
    parser.add_argument("--device-tunnel", default="VISA",
                        help="Connection tunnel type (VISA or SOCKET)")
    parser.add_argument("--device-address", required=True,
                        help="VISA address (e.g. TCPIP0::192.168.1.100::INSTR) "
                             "or SOCKET IP (e.g. 127.0.0.1)")
    parser.add_argument("--device-port", type=int, default=5025,
                        help="Port for SOCKET tunnel (default 5025)")
    parser.add_argument("--averages", type=int, default=1,
                        help="Number of averages")
    parser.add_argument("--start-freq", type=float, required=True,
                        help="Start frequency in Hz")
    parser.add_argument("--stop-freq", type=float, required=True,
                        help="Stop frequency in Hz")
    parser.add_argument("--sweep-type", default="LIN", choices=["LIN", "LOG"],
                        help="Sweep type (Linear/Log)")
    parser.add_argument("--sweep-points", type=int, default=201,
                        help="Number of sweep points")
    parser.add_argument("--ifbw", type=float, default=10000,
                        help="IF Bandwidth in Hz")
    parser.add_argument("--variable-amp",
                        help="Variable amplifier setting (reserved)")
    parser.add_argument("--source-level", type=float, default=-5.0,
                        help="Source power level in dBm")
    parser.add_argument("--calibration",
                        help="Filename of local calibration file to load (e.g. 'cal.cor')")
    parser.add_argument("--output-file", required=True,
                        help="Output filename for .s2p data")
    return parser.parse_args()


def configure_instrument(inst, args):
    # 1. Reset and Identification
    inst.write("*CLS")
    idn = inst.query("*IDN?")
    print(f"Connected to: {idn.strip()}")

    # 2. Set Mode to VNA
    print("Setting mode to VNA...")
    inst.write(":INSTrument:SELect VNA")
    time.sleep(3)

    # 3. Frequency Configuration
    inst.write(f":SENSe1:FREQuency:STARt {args.start_freq}")
    inst.write(f":SENSe1:FREQuency:STOP {args.stop_freq}")

    # 4. Bandwidth and Power
    inst.write(f":SENSe1:BWIDth:RESolution {args.ifbw}")
    inst.write(f":SOURce1:POWer:LEVel:IMMediate:AMPLitude {args.source_level}")

    # 5. Sweep Points
    inst.write(f":SENSe1:SWEep:POINts {args.sweep_points}")

    # 6. Averaging
    if args.averages > 1:
        inst.write(f":SENSe1:AVERage:COUNt {args.averages}")
        inst.write(":SENSe1:AVERage:STATe ON")
    else:
        inst.write(":SENSe1:AVERage:STATe OFF")

    # 7. Sweep type
    if args.sweep_type == "LOG":
        inst.write(":DISP:WIND:TRAC:X:SPAC LOG")
    else:
        inst.write(":DISP:WIND:TRAC:X:SPAC LIN")

    # 8. Calibration (if requested)
    if args.calibration:
        print(f"Loading calibration: {args.calibration}")
        inst.write(f":MMEMory:LOAD COR, \"{args.calibration}\"")
        inst.write(":CORRection:COLLect:SAVE")

    # 9. Configure traces for S-Parameters
    inst.write(":CALCulate1:PARameter:COUNt 4")
    inst.write(":CALCulate1:PARameter1:DEFine S11")
    inst.write(":CALCulate1:PARameter2:DEFine S21")
    inst.write(":CALCulate1:PARameter3:DEFine S21")
    inst.write(":CALCulate1:PARameter4:DEFine S11")

    for i in range(1, 5):
        inst.write(f":CALCulate1:PARameter{i}:SELect")
        inst.write(":CALCulate1:SELected:FORMat SCOMplex")


def perform_measurement(inst):
    print("Performing measurement...")
    inst.write(":INITiate1:CONTinuous OFF")
    inst.write(":INITiate1:IMMediate")
    inst.query("*OPC?")


def retrieve_data(inst):
    print("Retrieving trace data...")
    s_params = {}
    trace_map = {1: 's11', 2: 's21', 3: 's12', 4: 's22'}

    for trace_idx, s_name in trace_map.items():
        inst.write(f":CALCulate1:PARameter{trace_idx}:SELect")
        data = inst.query_ascii_values(":CALCulate1:SELected:DATA:FDATa?")
        s_params[s_name] = data

    return s_params


def write_s2p(filename, freqs, s_data):
    print(f"Exporting to {filename}...")
    with open(filename, 'w') as f:
        f.write("! Touchstone file generated by xDriver.py\n")
        f.write("# Hz S RI R 50\n")
        f.write("! Freq ReS11 ImS11 ReS21 ImS21 ReS12 ImS12 ReS22 ImS22\n")

        num_points = len(freqs)

        for i in range(num_points):
            idx = i * 2
            line = f"{freqs[i]:.6e} "
            line += f"{s_data['s11'][idx]:.6f} {s_data['s11'][idx+1]:.6f} "
            line += f"{s_data['s21'][idx]:.6f} {s_data['s21'][idx+1]:.6f} "
            line += f"{s_data['s12'][idx]:.6f} {s_data['s12'][idx+1]:.6f} "
            line += f"{s_data['s22'][idx]:.6f} {s_data['s22'][idx+1]:.6f}"
            f.write(line + "\n")


def main():
    args = parse_arguments()
    tunnel = args.device_tunnel.upper()

    inst = None
    rm = None

    if tunnel == "SOCKET":
        # --- Raw TCP socket mode (no pyvisa needed) ---
        print(f"Connecting via SOCKET to {args.device_address}:{args.device_port} ...")
        inst = SocketSCPI(args.device_address, args.device_port)

    elif tunnel == "VISA":
        # --- PyVISA mode ---
        import pyvisa
        rm = pyvisa.ResourceManager()
        inst = rm.open_resource(args.device_address)
        inst.timeout = 20000

    else:
        print(f"Unsupported tunnel type: {tunnel} (use VISA or SOCKET)")
        sys.exit(1)

    try:
        configure_instrument(inst, args)
        time.sleep(10)

        if args.averages > 1:
            s_data_bf = {}
            for i in range(args.averages):
                print(f"Acquisition {i+1} of {args.averages}...")
                perform_measurement(inst)
                s_data = retrieve_data(inst)
                for k in s_data:
                    if k not in s_data_bf:
                        s_data_bf[k] = s_data[k]
                    else:
                        s_data_bf[k] = [
                            s_data_bf[k][j] + s_data[k][j]
                            for j in range(len(s_data[k]))
                        ]
            s_data = {
                k: [v / args.averages for v in s_data_bf[k]]
                for k in s_data_bf
            }
        else:
            perform_measurement(inst)
            s_data = retrieve_data(inst)

        # Generate frequency list
        freqs = []
        if args.sweep_type == "LIN":
            if args.sweep_points > 1:
                step = (args.stop_freq - args.start_freq) / (args.sweep_points - 1)
                freqs = [args.start_freq + i * step for i in range(args.sweep_points)]
            else:
                freqs = [args.start_freq]
        else:
            if args.sweep_points > 1:
                import numpy as np
                freqs = np.logspace(
                    np.log10(args.start_freq),
                    np.log10(args.stop_freq),
                    args.sweep_points
                ).tolist()
            else:
                freqs = [args.start_freq]

        write_s2p(args.output_file, freqs, s_data)

        # Restore continuous sweep
        inst.write(":INITiate1:CONTinuous ON")
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if inst is not None:
            inst.close()
        if rm is not None:
            rm.close()


if __name__ == "__main__":
    main()
