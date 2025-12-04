# xDrviver/VNA_Class/SVA1000X.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# device-type VNA
# model SVA1000X
# tunnel VISA socket
# average support
# start-freq 1000000
# end-freq 1500000000
# sweep-type LIN LOG
# sweep-points 101 201 301 401 501
# ifbw 1000 3000 10000 30000 100000
# variable-amp reserved
# source-level -30 -20 -10 -5 0 5 10

import argparse
import sys
import time
import pyvisa
import struct

def parse_arguments():
    parser = argparse.ArgumentParser(description="Siglent VNA S2P Measurement Driver")
    parser.add_argument("--device-type", default="SVA1000X", help="Device model type")
    parser.add_argument("--device-tunnel", default="VISA", help="Connection tunnel type")
    parser.add_argument("--device-address", required=True, help="VISA Resource Address (e.g., TCPIP0::192.168.1.100::INSTR)")
    parser.add_argument("--averages", type=int, default=1, help="Number of averages")
    parser.add_argument("--start-freq", type=float, required=True, help="Start frequency in Hz")
    parser.add_argument("--stop-freq", type=float, required=True, help="Stop frequency in Hz")
    parser.add_argument("--sweep-type", default="LIN", choices=["LIN", "LOG"], help="Sweep type (Linear/Log)")
    parser.add_argument("--sweep-points", type=int, default=201, help="Number of sweep points")
    parser.add_argument("--ifbw", type=float, default=10000, help="IF Bandwidth in Hz")
    parser.add_argument("--variable-amp", help="Variable amplifier setting (reserved)")
    parser.add_argument("--source-level", type=float, default=-5.0, help="Source power level in dBm")
    parser.add_argument("--calibration", help="Filename of local calibration file to load (e.g., 'cal.cor')")
    parser.add_argument("--output-file", required=True, help="Output filename for .s2p data")
    return parser.parse_args()

def configure_instrument(inst, args):
    # 1. Reset and Identification
    inst.write("*CLS")
    idn = inst.query("*IDN?")
    print(f"Connected to: {idn.strip()}")

    # [cite_start]2. Set Mode to VNA [cite: 295]
    print("Setting mode to VNA...")
    inst.write(":INSTrument:SELect VNA")
    time.sleep(3) # Allow time for mode switch

    # 3. Frequency Configuration
    # [cite_start]Set Start Frequency [cite: 481]
    inst.write(f":SENSe1:FREQuency:STARt {args.start_freq}")
    # [cite_start]Set Stop Frequency [cite: 482]
    inst.write(f":SENSe1:FREQuency:STOP {args.stop_freq}")
    
    # 4. Bandwidth and Power
    # Set IF Bandwidth. [cite_start]Note: Manual section 5.3.1 implies query, but typically setting follows same syntax[cite: 489].
    # Using specific command structure for VNA mode if standard BWIDth is ambiguous.
    inst.write(f":SENSe1:BWIDth:RESolution {args.ifbw}")
    
    # [cite_start]Set Source Power [cite: 493]
    inst.write(f":SOURce1:POWer:LEVel:IMMediate:AMPLitude {args.source_level}")

    # 5. Sweep Configuration
    # [cite_start]Set Sweep Points [cite: 491]
    inst.write(f":SENSe1:SWEep:POINts {args.sweep_points}")
    
    # 6. Averaging Configuration
    if args.averages > 1:
        # [cite_start]Set Average Count [cite: 506]
        inst.write(f":SENSe1:AVERage:COUNt {args.averages}")
        # [cite_start]Enable Averaging [cite: 507]
        inst.write(":SENSe1:AVERage:STATe ON")
    else:
        inst.write(":SENSe1:AVERage:STATe OFF")

    # 7. Calibration Loading (if requested)
    if args.calibration:
        print(f"Loading calibration: {args.calibration}")
        # [cite_start]Load COR file [cite: 289]
        inst.write(f":MMEMory:LOAD COR, \"{args.calibration}\"")
        # [cite_start]Apply calibration [cite: 537]
        inst.write(":CORRection:COLLect:SAVE")

    # 8. Configure Traces for S-Parameters (S11, S21, S12, S22)
    # [cite_start]We need 4 traces to capture all S-parameters for s2p [cite: 495]
    inst.write(":CALCulate1:PARameter:COUNt 4")

    # [cite_start]Define parameters for traces [cite: 523]
    # Trace 1 -> S11
    inst.write(":CALCulate1:PARameter1:DEFine S11")
    # Trace 2 -> S21
    inst.write(":CALCulate1:PARameter2:DEFine S21")
    # Trace 3 -> S21
    inst.write(":CALCulate1:PARameter3:DEFine S21")
    # Trace 4 -> S11
    inst.write(":CALCulate1:PARameter4:DEFine S11")

    # [cite_start]Set Format to Real/Imag for data extraction [cite: 524]
    # SCOMplex returns Real and Imaginary parts, which is ideal for S2P generation
    for i in range(1, 5):
        inst.write(f":CALCulate1:PARameter{i}:SELect")
        inst.write(":CALCulate1:SELected:FORMat SCOMplex")

def perform_measurement(inst):
    print("Performing measurement...")
    # [cite_start]Set to Single Sweep Mode [cite: 492]
    inst.write(":INITiate1:CONTinuous OFF")
    
    # [cite_start]Trigger Sweep [cite: 491]
    inst.write(":INITiate1:IMMediate")
    
    # [cite_start]Wait for operation complete [cite: 270]
    inst.query("*OPC?")

def retrieve_data(inst):
    print("Retrieving trace data...")
    s_params = {}
    
    # Map trace indices to S-parameters
    trace_map = {1: 's11', 2: 's21', 3: 's12', 4: 's22'}

    for trace_idx, s_name in trace_map.items():
        # [cite_start]Select the trace [cite: 494]
        inst.write(f":CALCulate1:PARameter{trace_idx}:SELect")
        
        # [cite_start]Query Formatted Data (Real, Imag pairs) [cite: 501]
        # Using query_ascii_values to handle the comma-separated string automatically
        data = inst.query_ascii_values(":CALCulate1:SELected:DATA:FDATa?")
        s_params[s_name] = data
        
    return s_params

def write_s2p(filename, freqs, s_data):
    print(f"Exporting to {filename}...")
    with open(filename, 'w') as f:
        # Header
        f.write("! Touchstone file generated by xDriver.py\n")
        f.write("# Hz S RI R 50\n")
        f.write("! Freq ReS11 ImS11 ReS21 ImS21 ReS12 ImS12 ReS22 ImS22\n")

        num_points = len(freqs)
        
        # Iterate through points
        # Note: s_data contains flat lists [Re1, Im1, Re2, Im2...]
        for i in range(num_points):
            idx = i * 2
            line = f"{freqs[i]:.6e} "
            
            # S11 (Re, Im)
            line += f"{s_data['s11'][idx]:.6f} {s_data['s11'][idx+1]:.6f} "
            # S21 (Re, Im)
            line += f"{s_data['s21'][idx]:.6f} {s_data['s21'][idx+1]:.6f} "
            # S12 (Re, Im)
            line += f"{s_data['s12'][idx]:.6f} {s_data['s12'][idx+1]:.6f} "
            # S22 (Re, Im)
            line += f"{s_data['s22'][idx]:.6f} {s_data['s22'][idx+1]:.6f}"
            
            f.write(line + "\n")

def main():
    args = parse_arguments()
    rm = pyvisa.ResourceManager()

    try:
        inst = rm.open_resource(args.device_address)
        # Increase timeout for slow sweeps/averaging
        inst.timeout = 20000 
        
        configure_instrument(inst, args)
        
        if args.averages > 1:
            s_data_bf = {}
            for i in range(args.averages):
                print(f"Acquisition {i+1} of {args.averages}...")
                perform_measurement(inst)
                s_data = retrieve_data(inst)
                # 累加s_data到s_data_bf
                for k in s_data:
                    if k not in s_data_bf:
                        s_data_bf[k] = s_data[k]
                    else:
                        s_data_bf[k] = [s_data_bf[k][j] + s_data[k][j] for j in range(len(s_data[k]))]
            s_data = {k: [v / args.averages for v in s_data_bf[k]] for k in s_data_bf}
        else:
            perform_measurement(inst)
            s_data = retrieve_data(inst)

        # Generate Frequency List (Linear)
        freqs = []
        if args.sweep_type == "LIN":
            if args.sweep_points > 1:
                step = (args.stop_freq - args.start_freq) / (args.sweep_points - 1)
                freqs = [args.start_freq + i * step for i in range(args.sweep_points)]
            else:
                freqs = [args.start_freq]
        else:
            # Generate Logarithmic frequency list
            if args.sweep_points > 1:
                import numpy as np
                freqs = np.logspace(np.log10(args.start_freq), np.log10(args.stop_freq), args.sweep_points).tolist()
            else:
                freqs = [args.start_freq]

        write_s2p(args.output_file, freqs, s_data)
        
        # Restore Continuous Sweep
        inst.write(":INITiate1:CONTinuous ON")
        
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if 'inst' in locals():
            inst.close()
        if 'rm' in locals():
            rm.close()

if __name__ == "__main__":
    main()