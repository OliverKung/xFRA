# xConvCal.py - VNA Calibration Algorithm
# Implements OSL (1-port) and SOLT (2-port) calibration
# Based on LibreVNA reference implementation

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Tuple
import math


# =============================================================================
# Ideal Standard Models
# =============================================================================

def ideal_open(freq: np.ndarray, z0: float = 50.0) -> np.ndarray:
    """Ideal Open standard: Gamma = +1.0"""
    return np.ones_like(freq, dtype=np.complex128)


def ideal_short(freq: np.ndarray, z0: float = 50.0) -> np.ndarray:
    """Ideal Short standard: Gamma = -1.0"""
    return -np.ones_like(freq, dtype=np.complex128)


def ideal_load(freq: np.ndarray, z0: float = 50.0) -> np.ndarray:
    """Ideal Load standard: Gamma = 0.0"""
    return np.zeros_like(freq, dtype=np.complex128)


def ideal_through(freq: np.ndarray, z0: float = 50.0) -> Dict[str, np.ndarray]:
    """Ideal Through: perfect transmission, no reflection"""
    n = len(freq)
    return {
        "S11": np.zeros(n, dtype=np.complex128),
        "S12": np.ones(n, dtype=np.complex128),
        "S21": np.ones(n, dtype=np.complex128),
        "S22": np.zeros(n, dtype=np.complex128),
    }


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class CalPoint:
    """Single frequency point calibration error terms.
    D = Directivity, R = Reflection Tracking, S = Source Match,
    L = Receiver Match (matrix), T = Transmission Tracking (matrix),
    I = Isolation (matrix)
    For 2-port: vectors are length 2, matrices are 2x2.
    """
    frequency: float
    D: np.ndarray   # Directivity, per port
    R: np.ndarray   # Reflection tracking, per port
    S: np.ndarray   # Source match, per port
    L: np.ndarray   # Receiver match, [i][j] = from port i+1 to port j+1
    T: np.ndarray   # Transmission tracking, [i][j]
    I: np.ndarray   # Isolation, [i][j]


@dataclass
class CalibrationResult:
    """Result of calibration computation."""
    cal_type: str  # "OSL" or "SOLT"
    freq: np.ndarray
    points: List[CalPoint] = field(default_factory=list)

    def get_freq_list(self) -> List[float]:
        return [p.frequency for p in self.points]

    def get_D(self, port: int) -> np.ndarray:
        port_idx = port - 1
        return np.array([p.D[port_idx] for p in self.points])

    def get_R(self, port: int) -> np.ndarray:
        port_idx = port - 1
        return np.array([p.R[port_idx] for p in self.points])

    def get_S(self, port: int) -> np.ndarray:
        port_idx = port - 1
        return np.array([p.S[port_idx] for p in self.points])

    def get_T(self, src: int, rcv: int) -> np.ndarray:
        return np.array([p.T[src-1][rcv-1] for p in self.points])

    def get_L(self, src: int, rcv: int) -> np.ndarray:
        return np.array([p.L[src-1][rcv-1] for p in self.points])

    def get_I(self, src: int, rcv: int) -> np.ndarray:
        return np.array([p.I[src-1][rcv-1] for p in self.points])


# =============================================================================
# Calibration Computation
# =============================================================================

class xConvCalibrator:
    """Solver for VNA calibration error terms."""

    def __init__(self, z0: float = 50.0):
        self.z0 = z0

    # ---- Helpers ----

    @staticmethod
    def _interpolate_complex(freq: np.ndarray, values: np.ndarray, target_freq: float) -> np.complex128:
        """Linear interpolation in magnitude/phase for a target frequency."""
        if target_freq <= freq[0]:
            return values[0]
        if target_freq >= freq[-1]:
            return values[-1]
        idx = np.searchsorted(freq, target_freq)
        lo, hi = idx - 1, idx
        if hi >= len(freq):
            return values[-1]
        alpha = (target_freq - freq[lo]) / (freq[hi] - freq[lo])
        # interpolate magnitude/phase
        mag_lo, ph_lo = np.abs(values[lo]), np.angle(values[lo])
        mag_hi, ph_hi = np.abs(values[hi]), np.angle(values[hi])
        mag = mag_lo * (1 - alpha) + mag_hi * alpha
        # handle phase wrap
        dph = ph_hi - ph_lo
        dph = (dph + np.pi) % (2 * np.pi) - np.pi
        ph = ph_lo + dph * alpha
        return mag * np.exp(1j * ph)

    @staticmethod
    def _read_s2p_single(filepath: str) -> Tuple[np.ndarray, Dict[str, np.ndarray], float]:
        """Read a 2-port s2p file and return (freq, S-dict, z0)."""
        from xConv.xConv import xConvS2PReader
        r = xConvS2PReader(filepath)
        d = r.read()
        return d["freq"], {"S11": d["s11"], "S12": d["s12"], "S21": d["s21"], "S22": d["s22"]}, d["z0"]

    # ---- OSL (1-port) ----

    def compute_osl_1port(self,
                          freq: np.ndarray,
                          o_m: np.ndarray,  # measured Open S11
                          s_m: np.ndarray,  # measured Short S11
                          l_m: np.ndarray,  # measured Load S11
                          o_c: Optional[np.ndarray] = None,  # actual Open
                          s_c: Optional[np.ndarray] = None,  # actual Short
                          l_c: Optional[np.ndarray] = None,  # actual Load
                          ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute OSL error terms for a single port.
        Returns (D, S, R) - Directivity, Source Match, Reflection Tracking.
        If ideal values not provided, uses ideal model.
        """
        if o_c is None:
            o_c = ideal_open(freq, self.z0)
        if s_c is None:
            s_c = ideal_short(freq, self.z0)
        if l_c is None:
            l_c = ideal_load(freq, self.z0)

        denom = (l_c * o_c * (o_m - l_m) +
                 l_c * s_c * (l_m - s_m) +
                 o_c * s_c * (s_m - o_m))

        D = ((l_c * o_m * (s_m * (o_c - s_c) + l_m * s_c) -
              l_c * o_c * l_m * s_m +
              o_c * l_m * s_c * (s_m - o_m))) / denom

        S = (l_c * (o_m - s_m) + o_c * (s_m - l_m) + s_c * (l_m - o_m)) / denom

        delta = (l_c * l_m * (o_m - s_m) +
                 o_c * o_m * (s_m - l_m) +
                 s_c * s_m * (l_m - o_m)) / denom

        R = D * S - delta

        return D, S, R

    # ---- SOLT (2-port) ----

    def compute_solt(self,
                     port1: Dict[str, np.ndarray],  # {"open": o_m[1], "short": s_m[1], "load": l_m[1]}
                     port2: Dict[str, np.ndarray],
                     through: Dict[str, np.ndarray],  # {"S11": ..., "S21": ..., ...}
                     isolation: Optional[np.ndarray] = None,  # measured isolation S21
                     through_actual: Optional[Dict[str, np.ndarray]] = None,
                     ) -> CalibrationResult:
        """Compute full SOLT calibration.
        port1, port2: dicts with keys "open", "short", "load" -> S11 measured data.
        through: measured through S-params.
        """
        # All should share same frequency array
        freq = port1["freq"] if "freq" in port1 else None
        if freq is None:
            raise ValueError("port1 must contain 'freq' key")
        n = len(freq)

        # Compute OSL for each port
        D1, S1, R1 = self.compute_osl_1port(freq, port1["open"], port1["short"], port1["load"])
        D2, S2, R2 = self.compute_osl_1port(freq, port2["open"], port2["short"], port2["load"])

        # Through standard S-params (actual, or ideal if not provided)
        th_ideal = through_actual if through_actual is not None else ideal_through(freq, self.z0)

        # Through measurement
        S11_meas = through["S11"]
        S21_meas = through["S21"]

        iso = np.zeros(n, dtype=np.complex128) if isolation is None else isolation

        # Through ideal S-params
        det_S = th_ideal["S11"] * th_ideal["S22"] - th_ideal["S21"] * th_ideal["S12"]

        # Port 1 -> Port 2 (forward)
        denom_L12 = ((S11_meas - D1) * (th_ideal["S22"] - S1 * det_S) - det_S * R1)
        L12 = np.where(
            np.abs(denom_L12) > 1e-30,
            ((S11_meas - D1) * (1.0 - S1 * th_ideal["S11"]) - th_ideal["S11"] * R1) / denom_L12,
            0.0
        )

        T12 = np.where(
            np.abs(th_ideal["S21"]) > 1e-30,
            (S21_meas - iso) * (1.0 - S1 * th_ideal["S11"] - L12 * th_ideal["S22"] +
                                S1 * L12 * det_S) / th_ideal["S21"],
            1.0
        )

        # Port 2 -> Port 1 (reverse) - same through, swapped
        # Assume through is symmetric: S11<->S22, S21<->S12
        S22_meas = through["S22"]
        S12_meas = through["S12"]

        denom_L21 = ((S22_meas - D2) * (th_ideal["S11"] - S2 * det_S) - det_S * R2)
        L21 = np.where(
            np.abs(denom_L21) > 1e-30,
            ((S22_meas - D2) * (1.0 - S2 * th_ideal["S22"]) - th_ideal["S22"] * R2) / denom_L21,
            0.0
        )

        T21 = np.where(
            np.abs(th_ideal["S12"]) > 1e-30,
            (S12_meas - iso) * (1.0 - S2 * th_ideal["S22"] - L21 * th_ideal["S11"] +
                                S2 * L21 * det_S) / th_ideal["S12"],
            1.0
        )

        # Build CalPoint list
        result = CalibrationResult(cal_type="SOLT", freq=freq)
        for i in range(n):
            D_vec = np.array([D1[i], D2[i]])
            R_vec = np.array([R1[i], R2[i]])
            S_vec = np.array([S1[i], S2[i]])
            L_mat = np.array([[0.0, L12[i]], [L21[i], 0.0]])
            T_mat = np.array([[1.0, T12[i]], [T21[i], 1.0]])
            I_mat = np.array([[0.0, iso[i]], [iso[i], 0.0]])
            result.points.append(CalPoint(
                frequency=freq[i], D=D_vec, R=R_vec, S=S_vec,
                L=L_mat, T=T_mat, I=I_mat
            ))
        return result

    # ---- Through Normalization ----

    def compute_through_normalization(self,
                                      freq: np.ndarray,
                                      through: Dict[str, np.ndarray],
                                      ) -> CalibrationResult:
        """Simple through normalization (no SOL)."""
        n = len(freq)
        th_ideal = ideal_through(freq, self.z0)

        T12 = np.where(np.abs(th_ideal["S21"]) > 1e-30,
                       through["S21"] / th_ideal["S21"], 1.0)
        T21 = np.where(np.abs(th_ideal["S12"]) > 1e-30,
                       through["S12"] / th_ideal["S12"], 1.0)

        result = CalibrationResult(cal_type="ThroughNormalization", freq=freq)
        for i in range(n):
            D_vec = np.array([0.0, 0.0])
            R_vec = np.array([1.0, 1.0])
            S_vec = np.array([0.0, 0.0])
            L_mat = np.zeros((2, 2), dtype=np.complex128)
            T_mat = np.array([[1.0, T12[i]], [T21[i], 1.0]])
            I_mat = np.zeros((2, 2), dtype=np.complex128)
            result.points.append(CalPoint(
                frequency=freq[i], D=D_vec, R=R_vec, S=S_vec,
                L=L_mat, T=T_mat, I=I_mat
            ))
        return result

    # ---- Correction (Apply calibration to measurement) ----

    @staticmethod
    def correct_measurement(raw_s: np.ndarray,  # 2x2 raw S-param matrix
                            cal_point: CalPoint,
                            ) -> np.ndarray:
        """Apply calibration error terms to a single-point raw measurement.
        Returns corrected 2x2 S-param matrix.

        Based on wave formalism from:
        "Multi-Port Calibration Techniques for Differential Parameter
         Measurements with Network Analyzers"
        """
        n = 2  # 2-port
        S = raw_s.copy()
        a = np.zeros((n, n), dtype=np.complex128)
        b = np.zeros((n, n), dtype=np.complex128)

        # Remove isolation
        for i in range(n):
            for j in range(n):
                if i != j:
                    S[j, i] -= cal_point.I[i, j]

        # Assemble wave matrices
        for i in range(n):
            for j in range(n):
                if i == j:
                    # Exciting port
                    a[j, i] = 1.0 + cal_point.S[i] / cal_point.R[i] * (S[j, i] - cal_point.D[i])
                    b[j, i] = (1.0 / cal_point.R[i]) * (S[j, i] - cal_point.D[i])
                else:
                    # Receiving port
                    denom = cal_point.T[i, j]
                    if np.abs(denom) > 1e-30:
                        a[j, i] = cal_point.L[i, j] * S[j, i] / denom
                        b[j, i] = S[j, i] / denom
                    else:
                        a[j, i] = 0.0
                        b[j, i] = 0.0

        # Corrected S = b * a^(-1)
        try:
            a_inv = np.linalg.inv(a)
            S_corr = b @ a_inv
        except np.linalg.LinAlgError:
            S_corr = np.zeros_like(S)

        return S_corr

    def correct_s2p_full(self,
                         freq: np.ndarray,
                         s_params: Dict[str, np.ndarray],  # raw S11, S12, S21, S22
                         cal: CalibrationResult,
                         ) -> Dict[str, np.ndarray]:
        """Apply calibration to a full frequency sweep of raw S-params."""
        n = len(freq)
        s11_corr = np.zeros(n, dtype=np.complex128)
        s12_corr = np.zeros(n, dtype=np.complex128)
        s21_corr = np.zeros(n, dtype=np.complex128)
        s22_corr = np.zeros(n, dtype=np.complex128)

        for idx in range(n):
            f = freq[idx]
            raw = np.array([
                [s_params["S11"][idx], s_params["S12"][idx]],
                [s_params["S21"][idx], s_params["S22"][idx]],
            ])

            # Find closest calibration point
            cal_freqs = np.array([p.frequency for p in cal.points])
            cal_idx = np.argmin(np.abs(cal_freqs - f))
            cal_pt = cal.points[cal_idx]

            corr = self.correct_measurement(raw, cal_pt)
            s11_corr[idx] = corr[0, 0]
            s12_corr[idx] = corr[0, 1]
            s21_corr[idx] = corr[1, 0]
            s22_corr[idx] = corr[1, 1]

        return {"S11": s11_corr, "S12": s12_corr, "S21": s21_corr, "S22": s22_corr}

    # ---- High-Level Entry Points ----

    def calibrate_from_files(self,
                             cal_type: str,
                             files: Dict[str, str],  # key->filepath
                             ) -> CalibrationResult:
        """Main entry point: compute calibration from s2p files.

        files dict keys for SOLT:
          "short1", "open1", "load1", "short2", "open2", "load2", "through", "isolation"

        files dict keys for OSL:
          "short1", "open1", "load1"
        """
        if cal_type == "OSL":
            return self._calibrate_osl_from_files(files)
        elif cal_type == "SOLT":
            return self._calibrate_solt_from_files(files)
        else:
            raise ValueError(f"Unknown calibration type: {cal_type}")

    def _calibrate_osl_from_files(self, files: Dict[str, str]) -> CalibrationResult:
        """OSL 1-port calibration from files."""
        freq, s_short, _ = self._read_s2p_single(files["short1"])
        _, s_open, _ = self._read_s2p_single(files["open1"])
        _, s_load, _ = self._read_s2p_single(files["load1"])

        D, S, R = self.compute_osl_1port(
            freq, s_open["S11"], s_short["S11"], s_load["S11"]
        )

        result = CalibrationResult(cal_type="OSL", freq=freq)
        for i in range(len(freq)):
            D_vec = np.array([D[i]])
            R_vec = np.array([R[i]])
            S_vec = np.array([S[i]])
            L_mat = np.zeros((1, 1), dtype=np.complex128)
            T_mat = np.ones((1, 1), dtype=np.complex128)
            I_mat = np.zeros((1, 1), dtype=np.complex128)
            result.points.append(CalPoint(
                frequency=freq[i], D=D_vec, R=R_vec, S=S_vec,
                L=L_mat, T=T_mat, I=I_mat
            ))
        return result

    def _calibrate_solt_from_files(self, files: Dict[str, str]) -> CalibrationResult:
        """SOLT 2-port calibration from files."""
        # Read port 1
        freq, s_short1, _ = self._read_s2p_single(files["short1"])
        _, s_open1, _ = self._read_s2p_single(files["open1"])
        _, s_load1, _ = self._read_s2p_single(files["load1"])

        # Read port 2
        _, s_short2, _ = self._read_s2p_single(files["short2"])
        _, s_open2, _ = self._read_s2p_single(files["open2"])
        _, s_load2, _ = self._read_s2p_single(files["load2"])

        # Read through
        _, s_through, _ = self._read_s2p_single(files["through"])

        # Read isolation (optional)
        iso = None
        if "isolation" in files and files["isolation"]:
            _, s_iso, _ = self._read_s2p_single(files["isolation"])
            iso = s_iso["S21"]

        return self.compute_solt(
            {"freq": freq, "open": s_open1["S11"], "short": s_short1["S11"], "load": s_load1["S11"]},
            {"freq": freq, "open": s_open2["S11"], "short": s_short2["S11"], "load": s_load2["S11"]},
            s_through,
            isolation=iso,
        )

    # ---- Export calibration to s2p ----

    def export_cal_to_s2p(self, cal: CalibrationResult, output_path: str):
        """Export calibration error terms as a Touchstone s2p file."""
        with open(output_path, "w") as f:
            f.write("! xFRA Calibration Matrix\n")
            f.write("! Type: {}\n".format(cal.cal_type))
            f.write("# HZ S RI R 50\n")

            for pt in cal.points:
                f.write("{:.6e} ".format(pt.frequency))

                # For 2-port: S11 = D[0], S12 = T[0][1], S21 = T[1][0], S22 = D[1]
                if len(pt.D) >= 2:
                    f.write("{:.6e} {:.6e} ".format(pt.D[0].real, pt.D[0].imag))
                    f.write("{:.6e} {:.6e} ".format(pt.T[0][1].real, pt.T[0][1].imag))
                    f.write("{:.6e} {:.6e} ".format(pt.T[1][0].real, pt.T[1][0].imag))
                    f.write("{:.6e} {:.6e}".format(pt.D[1].real, pt.D[1].imag))
                else:
                    # 1-port: only S11 = D[0]
                    f.write("{:.6e} {:.6e} ".format(pt.D[0].real, pt.D[0].imag))
                    f.write("0.000000e+00 0.000000e+00 ")
                    f.write("0.000000e+00 0.000000e+00 ")
                    f.write("0.000000e+00 0.000000e+00")
                f.write("\n")


# =============================================================================
# Quick self-test
# =============================================================================

if __name__ == "__main__":
    # Test with known error terms: Gamma_m = D + R * Gamma_a / (1 - S * Gamma_a)
    freqs = np.logspace(3, 6, 11)

    D_true = 0.05 + 0.01j
    S_true = 0.03 + 0.005j
    R_true = 0.95 - 0.02j

    def apply_error(Gamma_a):
        return D_true + R_true * Gamma_a / (1 - S_true * Gamma_a)

    o_c = ideal_open(freqs)     # +1.0
    s_c = ideal_short(freqs)    # -1.0
    l_c = ideal_load(freqs)     # 0.0

    o_m = apply_error(o_c)
    s_m = apply_error(s_c)
    l_m = apply_error(l_c)

    c = xConvCalibrator()
    D, S, R = c.compute_osl_1port(freqs, o_m, s_m, l_m, o_c, s_c, l_c)

    print("OSL Test (known error box model):")
    print(f"  D: true={D_true}  computed={D[0]}")
    print(f"  S: true={S_true}  computed={S[0]}")
    print(f"  R: true={R_true}  computed={R[0]}")
    ok = all(abs(D - D_true) < 1e-9) and all(abs(S - S_true) < 1e-9) and all(abs(R - R_true) < 1e-9)
    print("  PASS" if ok else "  FAIL (numerical difference)")
