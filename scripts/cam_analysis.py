"""
Manufacturability numbers for 5-axis milling of the two impellers, from the same blade
geometry as the CAD curves (impeller_geometry.stage_blades).

    python scripts/cam_analysis.py      -> docs/cam_summary.json + printed summary

Everything here is a first-order planning estimate. The CAM system's own collision check,
swarf-error report and simulated cycle time replace these numbers once toolpaths exist.
"""
import json
import math

import numpy as np

import impeller_geometry as IG
import layout as LY

ROOT = IG.ROOT
PITCH = 2 * math.pi / 7

# ------------------------------------------------------------- design / process inputs
RHO_ALU = 2810.0                 # 7075-T6, kg/m3
FILLET_DRAWN = 1.0               # hub fillet on TC-101/102, mm
FILLET_REC = 1.5                 # recommended: lets the Ø3 finishing ball cut the fillet
ROUGH_STOCK = 0.30               # left on blades/hub after roughing, mm per side
TOOL_CLEAR = 0.5                 # minimum tool-to-blade clearance while roughing, mm
SCALLOP_FINISH = 0.004           # mm, about Ra 0.8 um on flow surfaces
SCALLOP_SEMI = 0.02
MOTION_FACTOR = 1.35             # 5-axis accel/decel, links, tool changes
BALANCE_G = 1.0                  # ISO 21940-11 grade (TC-101/102)
SPINDLE_RPM = 15000              # typical 5-axis trunnion machine with HSK-A63 spindle

# carbide tools in aluminium; F = rpm * flutes * fz (mm/min)
TOOLS = {
    "T1": dict(desc="Ø5 bull nose R0.5, 3 fl, 20 mm reach", d=5.0, r=0.5, flutes=3, fz=0.040, ap=1.0, ae=2.0),
    "T2": dict(desc="Ø3 bull nose R0.25, 3 fl, 20 mm reach", d=3.0, r=0.25, flutes=3, fz=0.020, ap=0.6, ae=1.0),
    "T3": dict(desc="Ø3 tapered ball R1.5, 2° per side, 2 fl", d=3.0, r=1.5, flutes=2, fz=0.025),
    "T4": dict(desc="Ø2 tapered ball R1.0, 3° per side, 2 fl", d=2.0, r=1.0, flutes=2, fz=0.015),
    "T5": dict(desc="Ø6 chamfer / deburr, 90°", d=6.0, r=0.0, flutes=4, fz=0.03),
}
for t in TOOLS.values():
    t["feed"] = SPINDLE_RPM * t["flutes"] * t["fz"]


def stepover(r, h):
    """Ball-end stepover for scallop height h."""
    return 2 * math.sqrt(max(2 * r * h - h * h, 0.0))


def polygon_area_centroid_r(zr):
    z, r = zr[:, 0], zr[:, 1]
    cross = z * np.roll(r, -1) - np.roll(z, -1) * r
    a = 0.5 * cross.sum()
    cr = ((r + np.roll(r, -1)) * cross).sum() / (6 * a)
    return abs(a), cr


def revolved_area(zr):
    """Surface area of a meridional line revolved 360 deg (Pappus)."""
    d = np.diff(zr, axis=0)
    ds = np.hypot(d[:, 0], d[:, 1])
    rm = 0.5 * (zr[1:, 1] + zr[:-1, 1])
    return float((2 * math.pi * rm * ds).sum())


def stage(i):
    g = IG.stage_blades(i)
    s, hub, shroud, L = g["s"], g["hub"], g["shroud"], g["L"]
    zh, th, bh, mh = g["main_h"]
    zs, ts, bs, ms = g["main_s"]
    ph, ps = IG.to_xyz(zh, th), IG.to_xyz(zs, ts)

    # rulings join equal-index hub and shroud camber points (the CAD boundary surface)
    rul = ps - ph
    height = np.linalg.norm(rul, axis=1)
    u = rul / height[:, None]
    nh = np.cross(np.gradient(ph, axis=0), u)
    ns = np.cross(np.gradient(ps, axis=0), u)
    nh /= np.linalg.norm(nh, axis=1)[:, None]
    ns /= np.linalg.norm(ns, axis=1)[:, None]
    twist = np.degrees(np.arccos(np.clip((nh * ns).sum(1), -1, 1)))   # non-developability

    # normal gap between neighbouring blades (main-main ahead of the splitter, main-splitter behind)
    spl = mh >= IG.SPLITTER_START
    gap_h = zh[:, 1] * np.where(spl, PITCH / 2, PITCH) * np.cos(np.radians(bh)) - IG.T_HUB
    gap_s = zs[:, 1] * np.where(ms >= IG.SPLITTER_START, PITCH / 2, PITCH) * np.cos(np.radians(bs)) - IG.T_SHROUD
    gap = np.minimum(gap_h, gap_s)
    k_crit = int(np.argmin(gap_h))

    # ruled blade surface area (one side), quads between consecutive rulings
    quad = 0.5 * (np.linalg.norm(np.cross(ph[1:] - ph[:-1], ps[:-1] - ph[:-1]), axis=1)
                  + np.linalg.norm(np.cross(ps[1:] - ps[:-1], ps[1:] - ph[1:]), axis=1))
    spl_q = 0.5 * (spl[1:].astype(float) + spl[:-1])
    a_main, a_spl = quad.sum(), (quad * spl_q).sum()
    t_mean = 0.5 * (IG.T_HUB + IG.T_SHROUD)
    v_blades = 7 * (a_main + a_spl) * t_mean

    # passage (hub-to-shroud annulus, 360 deg) and what the 5-axis machine removes
    poly = np.vstack([hub, shroud[::-1]])
    a_m, r_c = polygon_area_centroid_r(poly)
    v_annulus = 2 * math.pi * r_c * a_m
    v_remove = v_annulus - v_blades

    # finished part: hub body from bore to hub line, backplate, blades
    rb = LY.SHAFT_D_IMP / 2
    body = np.vstack([[[0, rb]], hub, [[L + LY.BACKPLATE_T, hub[-1, 1]], [L + LY.BACKPLATE_T, rb]]])
    a_b, r_b = polygon_area_centroid_r(body)
    v_part = 2 * math.pi * r_b * a_b + v_blades
    mass = v_part * 1e-9 * RHO_ALU

    # split roughing between T1 (where it fits with clearance) and T2 (rest)
    t1 = TOOLS["T1"]
    fits_t1 = (gap - 2 * ROUGH_STOCK - 2 * TOOL_CLEAR) >= t1["d"]
    w = np.ones(len(mh))
    frac_t1 = 0.85 * (w * fits_t1).sum() / w.sum()
    v_t1, v_t2 = v_remove * frac_t1, v_remove * (1 - frac_t1)

    def mrr(t):
        return t["ap"] * t["ae"] * t["feed"]

    # finishing areas
    a_hub_floor = revolved_area(hub) - 7 * (np.hypot(*np.diff(zh, axis=0).T).sum()
                                            + np.hypot(*np.diff(zh[spl], axis=0).T).sum()) * IG.T_HUB
    a_blade_sides = 2 * 7 * (a_main + a_spl)
    t3 = TOOLS["T3"]
    so_f, so_s = stepover(t3["r"], SCALLOP_FINISH), stepover(t3["r"], SCALLOP_SEMI)
    flank_err = {f"R{r:g}": float(r * (1 - math.cos(math.radians(twist.max() / 2)))) for r in (1.0, 1.5)}
    blade_len = 0.5 * (np.hypot(*np.diff(zh, axis=0).T).sum() + np.hypot(*np.diff(zs, axis=0).T).sum())
    fillet_len = 2 * 7 * (np.hypot(*np.diff(zh, axis=0).T).sum() + np.hypot(*np.diff(zh[spl], axis=0).T).sum())

    minutes = {
        "OP40-1 rough T1": v_t1 / mrr(t1),
        "OP40-2 rest-rough T2": v_t2 / mrr(TOOLS["T2"]),
        "OP40-3 semi-finish T3": (a_blade_sides + a_hub_floor) / (so_s * t3["feed"]),
        "OP40-4 finish hub T3": a_hub_floor / (so_f * t3["feed"]),
        "OP40-5 finish blades T3 (point)": a_blade_sides / (so_f * t3["feed"]),
        "OP40-6 fillet pencil T4 (only if R1.0 kept)": 3 * fillet_len / TOOLS["T4"]["feed"],
        "OP40-7 deburr T5": 2 * fillet_len / TOOLS["T5"]["feed"],
    }
    minutes = {k: v * MOTION_FACTOR for k, v in minutes.items()}
    flank_finish = MOTION_FACTOR * 28 * 2 * blade_len / (0.6 * t3["feed"])

    omega = IG.DP["inputs"]["speed_rpm"] * 2 * math.pi / 60
    e_per_um = BALANCE_G / omega * 1e3                        # permissible eccentricity, um
    return dict(
        stage=i, D2=s["D2"] * 1e3, b2=s["b2"] * 1e3, L=L,
        height_le=float(height[0]), height_te=float(height[-1]),
        crit_m=float(mh[k_crit]), crit_gap_hub=float(gap_h[k_crit]), crit_height=float(height[k_crit]),
        reach_over_d_T3=float(height[k_crit] / TOOLS["T3"]["d"]),
        twist_max=float(twist.max()), flank_error_mm=flank_err,
        flank_ok_R1p5=bool(flank_err["R1.5"] <= 0.05),
        blade_area_main_mm2=float(a_main), blade_area_splitter_mm2=float(a_spl),
        v_annulus_cm3=v_annulus / 1e3, v_blades_cm3=v_blades / 1e3, v_remove_cm3=v_remove / 1e3,
        frac_T1=float(frac_t1), part_volume_cm3=v_part / 1e3, mass_kg=mass,
        hub_floor_area_cm2=a_hub_floor / 100, blade_side_area_cm2=a_blade_sides / 100,
        stepover_finish_mm=so_f, stepover_semi_mm=so_s,
        minutes={k: round(v, 1) for k, v in minutes.items()},
        flank_finish_minutes=round(flank_finish, 1),
        balance_e_per_um=e_per_um, balance_U_gmm=mass * e_per_um,
        profile=dict(m=mh.tolist(), gap_hub=gap_h.tolist(), gap_shroud=gap_s.tolist(),
                     height=height.tolist(), twist=twist.tolist(), beta_hub=bh.tolist(),
                     r_hub=zh[:, 1].tolist()),
    )


def main():
    out = {"inputs": dict(spindle_rpm=SPINDLE_RPM, scallop_finish_mm=SCALLOP_FINISH,
                          rough_stock_mm=ROUGH_STOCK, motion_factor=MOTION_FACTOR,
                          fillet_drawn_mm=FILLET_DRAWN, fillet_recommended_mm=FILLET_REC,
                          balance_grade=BALANCE_G, density=RHO_ALU),
           "tools": TOOLS, "stage1": stage(1), "stage2": stage(2)}
    (ROOT / "docs" / "cam_summary.json").write_text(json.dumps(out, indent=1))
    for i in (1, 2):
        c = out[f"stage{i}"]
        tot = sum(v for k, v in c["minutes"].items() if "T4" not in k)
        print(f"stage {i}: tightest passage {c['crit_gap_hub']:.2f} mm at m={c['crit_m']:.2f} "
              f"(blade {c['crit_height']:.1f} mm tall, L/D {c['reach_over_d_T3']:.1f} for Ø3); "
              f"twist max {c['twist_max']:.1f} deg, flank error R1.5 {c['flank_error_mm']['R1.5']:.3f} mm; "
              f"remove {c['v_remove_cm3']:.1f} cm3 ({100 * c['frac_T1']:.0f} % with T1); "
              f"mass {c['mass_kg']:.3f} kg; 5-axis {tot:.0f} min (R1.5 fillets), "
              f"flank-finish alt {c['flank_finish_minutes']:.0f} min; "
              f"U_per {c['balance_U_gmm']:.3f} g.mm")


if __name__ == "__main__":
    main()
