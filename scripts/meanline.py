"""
Meanline sizing of a two-stage, oil-free, magnetic-bearing centrifugal compressor
in the class of the Danfoss Turbocor TTS350 used in the Trane TCAA air-cooled chiller
(R-513A, ~110 tons per compressor, IGVs + two in-line impellers + de-swirl vanes + volute).

This is NOT the OEM geometry. It is a physically consistent preliminary design built
from standard centrifugal-compressor correlations, so the CAD model and CFD have realistic
proportions and a defensible design point.

Run:   python scripts/meanline.py
Writes: docs/design_point.json
"""
import json
import math
from pathlib import Path

import CoolProp.CoolProp as CP

# R-513A = R-1234yf / R-134a, 56/44 % by mass (azeotrope)
AS = CP.AbstractState("HEOS", "R1234yf&R134a")
AS.set_mass_fractions([0.56, 0.44])

# ---------------- Design point: AHRI 550/590 air-cooled (44 F LWT, 95 F ambient) ----
TONS = 110.0                   # TCAA220BT = 165-240 tons on 2 compressors
Q_EVAP = TONS * 3.51685e3      # W
T_EVAP = 3.5 + 273.15          # saturated suction temperature, K (38 F)
T_COND = 51.5 + 273.15         # saturated discharge temperature, K (125 F, air-cooled)
SUPERHEAT = 3.0                # K at the impeller eye (motor-cooling gas returns to suction)
SUBCOOL = 5.0                  # K, IOM: integral subcooler
N_RPM = 30000                  # design speed; Turbocor TT-family runs roughly 18k-39k rpm

ETA_IMP_TT = 0.90              # impeller total-to-total isentropic efficiency
ETA_STAGE_TT = 0.80            # stage total-to-total (impeller + diffuser + de-swirl/volute)
Z_MAIN, Z_SPLIT = 7, 7         # main blades + splitter blades
BETA2B_DEG = 40.0              # exit blade angle (backsweep, measured from meridional)
PHI2 = 0.28                    # exit flow coefficient Cm2/U2
BLOCKAGE2 = 0.06               # exit blockage fraction
HUB_RATIO = (0.40, 0.48)       # eye hub/tip ratio, stage 1 and stage 2
DIFF_RATIO = 1.55              # vaneless diffuser exit radius / impeller tip radius
MECH_LOSS = 0.02               # mag-bearing + windage losses, fraction of gas power
MOTOR_VFD_EFF = 0.95           # PM motor x inverter


def _props():
    return dict(h=AS.hmass(), s=AS.smass(), rho=AS.rhomass(), T=AS.T(), P=AS.p(),
                a=AS.speed_sound())


def st(pair, a, b):
    if pair == CP.HmassSmass_INPUTS:
        return hs_flash(a, b)
    AS.update(pair, a, b)
    return _props()


_guess = [20.0, 290.0]


def hs_flash(h, s):
    """Vapour-phase (h, s) flash by Newton iteration on (rho, T).

    CoolProp's built-in HS flash for mixtures is ~100x slower than (rho, T) calls.
    Raises ValueError if the converged state lies inside the vapour dome.
    """
    rho, T = _guess
    for _ in range(50):
        AS.update(CP.DmassT_INPUTS, rho, T)
        fh, fs = AS.hmass() - h, AS.smass() - s
        if abs(fh) < 1e-3 and abs(fs) < 1e-6:
            break
        hr = AS.first_partial_deriv(CP.iHmass, CP.iDmass, CP.iT)
        hT = AS.first_partial_deriv(CP.iHmass, CP.iT, CP.iDmass)
        sr = AS.first_partial_deriv(CP.iSmass, CP.iDmass, CP.iT)
        sT = AS.first_partial_deriv(CP.iSmass, CP.iT, CP.iDmass)
        det = hr * sT - hT * sr
        drho = (fh * sT - hT * fs) / det
        dT = (hr * fs - fh * sr) / det
        rho = max(rho - drho, 0.3 * rho)
        T -= max(min(dT, 20.0), -20.0)
    else:
        raise ValueError("hs_flash did not converge")
    props = _props()
    AS.update(CP.QT_INPUTS, 1, T)
    if rho > AS.rhomass():
        raise ValueError("state is inside the vapour dome")
    _guess[:] = [rho, T]
    return props


def size_inlet(mdot, s0, hub_ratio, omega):
    """Pick the eye tip diameter that minimises inlet relative Mach number (IGVs open)."""
    best = None
    for d1t_mm in range(40, 150):
        d1t = d1t_mm / 1000
        area = math.pi / 4 * d1t ** 2 * (1 - hub_ratio ** 2)
        rho = s0["rho"]
        try:
            for _ in range(20):
                cm = mdot / (rho * area)
                s1 = st(CP.HmassSmass_INPUTS, s0["h"] - cm ** 2 / 2, s0["s"])
                rho = s1["rho"]
        except ValueError:  # eye too small: static state expands into the vapour dome
            continue
        u1t = omega * d1t / 2
        m1rel = math.hypot(cm, u1t) / s1["a"]
        if best is None or m1rel < best["M1rel"]:
            best = dict(D1t=d1t, D1h=d1t * hub_ratio, Cm1=cm, U1t=u1t,
                        W1t=math.hypot(cm, u1t), M1rel=m1rel, rho1=rho,
                        beta1t_deg=math.degrees(math.atan2(u1t, cm)),
                        beta1h_deg=math.degrees(math.atan2(u1t * hub_ratio, cm)))
    return best


def stage(mdot, inlet, D2, omega):
    """One stage at tip diameter D2. Returns exit geometry/velocities and exit total state."""
    U2 = omega * D2 / 2
    sigma = 1 - math.sqrt(math.cos(math.radians(BETA2B_DEG))) / (Z_MAIN + Z_SPLIT) ** 0.7  # Wiesner
    Cm2 = PHI2 * U2
    Ct2 = sigma * U2 - Cm2 * math.tan(math.radians(BETA2B_DEG))
    dh0 = U2 * Ct2                                   # Euler work, zero inlet swirl

    P02 = st(CP.HmassSmass_INPUTS, inlet["h"] + ETA_IMP_TT * dh0, inlet["s"])["P"]
    s02 = st(CP.HmassP_INPUTS, inlet["h"] + dh0, P02)
    C2 = math.hypot(Cm2, Ct2)
    s2 = st(CP.HmassSmass_INPUTS, s02["h"] - C2 ** 2 / 2, s02["s"])
    b2 = mdot / (s2["rho"] * math.pi * D2 * Cm2 * (1 - BLOCKAGE2))

    P03 = st(CP.HmassSmass_INPUTS, inlet["h"] + ETA_STAGE_TT * dh0, inlet["s"])["P"]
    out = st(CP.HmassP_INPUTS, inlet["h"] + dh0, P03)
    geo = dict(D2=D2, U2=U2, b2=b2, slip=sigma, Cm2=Cm2, Ct2=Ct2, C2=C2,
               M2abs=C2 / s2["a"], alpha2_deg=math.degrees(math.atan2(Ct2, Cm2)),
               work_kJkg=dh0 / 1e3, psi=dh0 / U2 ** 2, P_in=inlet["P"], P_out=P03,
               PR=P03 / inlet["P"], T_in=inlet["T"], T_out=out["T"], rho_in=inlet["rho"],
               rho2=s2["rho"], D3=DIFF_RATIO * D2, b3=0.9 * b2,
               flow_coeff=mdot / inlet["rho"] / (D2 ** 2 * U2))
    return geo, out


def main():
    P_ev = st(CP.QT_INPUTS, 1, T_EVAP)["P"]
    P_cd = st(CP.QT_INPUTS, 1, T_COND)["P"]
    suction = st(CP.PT_INPUTS, P_ev, T_EVAP + SUPERHEAT)
    h_liq = st(CP.PT_INPUTS, P_cd, T_COND - SUBCOOL)["h"]
    mdot = Q_EVAP / (suction["h"] - h_liq)
    omega = N_RPM * 2 * math.pi / 60

    # Both impellers share one tip diameter; bisect D2 so two stages reach condenser pressure.
    lo, hi = 0.05, 0.14
    for _ in range(35):
        D2 = 0.5 * (lo + hi)
        s1, mid = stage(mdot, suction, D2, omega)
        s2, dis = stage(mdot, mid, D2, omega)
        lo, hi = (D2, hi) if dis["P"] < P_cd else (lo, D2)
    s1.update(size_inlet(mdot, suction, HUB_RATIO[0], omega))
    s2.update(size_inlet(mdot, mid, HUB_RATIO[1], omega))

    gas_power = mdot * (dis["h"] - suction["h"])
    shaft_power = gas_power * (1 + MECH_LOSS)
    input_power = shaft_power / MOTOR_VFD_EFF
    h_dis_s = st(CP.PSmass_INPUTS, P_cd, suction["s"])["h"]

    result = dict(
        basis="Turbocor TTS350-class, Trane TCAA air-cooled chiller (TCA-SVX001C-EN)",
        inputs=dict(fluid="R-513A (R1234yf/R134a 56/44 wt%)", capacity_tons=TONS,
                    capacity_kW=Q_EVAP / 1e3, T_evap_C=T_EVAP - 273.15, T_cond_C=T_COND - 273.15,
                    superheat_K=SUPERHEAT, subcool_K=SUBCOOL, speed_rpm=N_RPM,
                    blades=f"{Z_MAIN} main + {Z_SPLIT} splitter", beta2b_deg=BETA2B_DEG,
                    eta_impeller_tt=ETA_IMP_TT, eta_stage_tt=ETA_STAGE_TT),
        cycle=dict(P_suction_kPa=P_ev / 1e3, P_discharge_kPa=P_cd / 1e3, PR_total=P_cd / P_ev,
                   mdot_kg_s=mdot, Q_suction_m3_s=mdot / suction["rho"],
                   T_suction_C=suction["T"] - 273.15, T_discharge_C=dis["T"] - 273.15,
                   rho_suction_kg_m3=suction["rho"]),
        power=dict(gas_kW=gas_power / 1e3, shaft_kW=shaft_power / 1e3, input_kW=input_power / 1e3,
                   overall_isentropic_eff=(h_dis_s - suction["h"]) / (dis["h"] - suction["h"]),
                   kW_per_ton=input_power / 1e3 / TONS, COP=Q_EVAP / input_power,
                   shaft_torque_Nm=shaft_power / omega),
        stage1=s1, stage2=s2,
    )
    out = Path(__file__).resolve().parent.parent / "docs" / "design_point.json"
    out.write_text(json.dumps(result, indent=2))

    c = result["cycle"]
    print(f"P_suc {c['P_suction_kPa']:.0f} kPa  P_dis {c['P_discharge_kPa']:.0f} kPa  PR {c['PR_total']:.2f}"
          f"  mdot {mdot:.3f} kg/s  Q_suc {c['Q_suction_m3_s']:.4f} m3/s")
    for name, s in (("Stage 1", s1), ("Stage 2", s2)):
        print(f"{name}: D2 {s['D2']*1e3:.1f} mm  U2 {s['U2']:.0f} m/s  b2 {s['b2']*1e3:.2f} mm  "
              f"D1t {s['D1t']*1e3:.0f} / D1h {s['D1h']*1e3:.1f} mm  PR {s['PR']:.3f}  "
              f"M1rel {s['M1rel']:.2f}  M2 {s['M2abs']:.2f}  alpha2 {s['alpha2_deg']:.1f}  "
              f"phi {s['flow_coeff']:.3f}  b1t {s['beta1t_deg']:.1f}  b1h {s['beta1h_deg']:.1f}")
    p = result["power"]
    print(f"Shaft {p['shaft_kW']:.1f} kW  input {p['input_kW']:.1f} kW  {p['kW_per_ton']:.3f} kW/ton  "
          f"torque {p['shaft_torque_Nm']:.1f} N.m  T_dis {c['T_discharge_C']:.1f} C")


if __name__ == "__main__":
    main()
