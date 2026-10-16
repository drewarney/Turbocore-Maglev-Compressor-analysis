"""
Turn CFD mass-averaged inlet/outlet totals into pressure ratio and real-gas
total-to-total isentropic efficiency for R-513A, and compare with the meanline.

Usage (values from CFD-Post: massFlowAve(Total Pressure in Stn Frame)@inlet, etc.):
    python scripts/cfd_postprocess.py --p0in 364.3 --t0in 279.65 --p0out 720.0 --t0out 306.5 \
        --mdot 3.343 --stage 1
Pressures in kPa (absolute), temperatures in K, mdot in kg/s (full wheel).
"""
import argparse
import json
from pathlib import Path

import CoolProp.CoolProp as CP

AS = CP.AbstractState("HEOS", "R1234yf&R134a")
AS.set_mass_fractions([0.56, 0.44])


def hs(p, t):
    AS.update(CP.PT_INPUTS, p, t)
    return AS.hmass(), AS.smass()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p0in", type=float, required=True)
    ap.add_argument("--t0in", type=float, required=True)
    ap.add_argument("--p0out", type=float, required=True)
    ap.add_argument("--t0out", type=float, required=True)
    ap.add_argument("--mdot", type=float, default=None)
    ap.add_argument("--stage", type=int, choices=(1, 2), default=None)
    a = ap.parse_args()

    h1, s1 = hs(a.p0in * 1e3, a.t0in)
    h2, _ = hs(a.p0out * 1e3, a.t0out)
    AS.update(CP.PSmass_INPUTS, a.p0out * 1e3, s1)
    h2s = AS.hmass()
    pr, eta = a.p0out / a.p0in, (h2s - h1) / (h2 - h1)
    print(f"PR_tt          = {pr:.4f}")
    print(f"eta_tt (real)  = {eta:.4f}")
    print(f"work dh0       = {(h2 - h1) / 1e3:.2f} kJ/kg")
    if a.mdot:
        print(f"gas power      = {a.mdot * (h2 - h1) / 1e3:.1f} kW")
    if a.stage:
        dp = json.loads((Path(__file__).resolve().parent.parent / "docs" / "design_point.json").read_text())
        st = dp[f"stage{a.stage}"]
        print(f"meanline stage {a.stage}: PR {st['PR']:.4f}, work {st['work_kJkg']:.2f} kJ/kg "
              f"(stage eta_tt assumed {dp['inputs']['eta_stage_tt']})")


if __name__ == "__main__":
    main()
