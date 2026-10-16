"""
Build the drawing set: drawings/Turbocor_drawing_set.pdf (+ PNG previews per sheet)
and export flow-path curves for SolidWorks / CFD.

    python scripts/meanline.py && python scripts/impeller_geometry.py && python scripts/make_drawings.py
"""
import math

import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

import layout as L
from drafting import Sheet, FILLS, INK, DIM

OUT = L.ROOT / "drawings"
OUT.mkdir(exist_ok=True)
DP, S1, S2 = L.DP, L.S1, L.S2
FP = L.flowpath()
VOL, VOL_Q = L.volute_sections()
DESWIRL_IN, _ = L.deswirl_angles()
TOTAL = 12


def fmt(v, n=1):
    return f"{v:.{n}f}"


# ------------------------------------------------------------------ shared shapes
def fluid_polygon():
    f = FP
    shroud = np.vstack([f["inlet_shr"], f["shr1"], [[L.D1_SHR_X, L.R2], [L.D1_SHR_X, L.R3]],
                        f["bend_out"], f["rc_shr"], f["shr2"],
                        [[L.D2_SHR_X, L.R2], [L.D2_SHR_X, L.R3]]])
    hub = np.vstack([[[L.D2_HUB_X, L.R3], [L.D2_HUB_X, L.R2]], f["hub2"][::-1],
                     f["rc_hub"][::-1], f["bend_in"][::-1],
                     [[L.D1_HUB_X, L.R3], [L.D1_HUB_X, L.R2]], f["hub1"][::-1],
                     f["nose"][::-1], [[L.NOSE_X0, 0], [0, 0]]])
    return np.vstack([shroud, hub])


def impeller_body(stage, x0):
    hub = FP["hub1"] if stage == 1 else FP["hub2"]
    rb = L.SHAFT_D_IMP / 2
    xb = x0 + L.IMP_L + L.BACKPLATE_T
    return np.vstack([[x0, rb], hub, [[xb, L.R2], [xb, rb]]])


def blade_region(stage):
    hub = FP["hub1"] if stage == 1 else FP["hub2"]
    shr = FP["imp_shr1"] if stage == 1 else FP["imp_shr2"]
    return np.vstack([hub, shr[::-1]])


def draw_rotor(v, labels=False):
    for x0, x1, d, name in L.SHAFT:
        fc = FILLS["magnet"] if "PM motor" in name else (
            FILLS["steel"] if "laminations" in name else FILLS["rotor"])
        v.mirror_rect(x0, 0, x1, d / 2, fc=fc, lw=0.45, z=6)
    t0, t1, od = L.THRUST_DISK
    v.mirror_rect(t0, 20, t1, od / 2, fc=FILLS["rotor"], lw=0.45, z=6)
    for st, x0 in ((1, L.IMP1_X0), (2, L.IMP2_X0)):
        v.mirror_poly(blade_region(st), fc=FILLS["blade"], lw=0.4, z=6)
        v.mirror_poly(impeller_body(st, x0), fc=FILLS["alu"], lw=0.6, hatch="////", z=7)
    v.mirror_poly(FP["nose"].tolist() + [[L.IMP1_X0, 0]], fc=FILLS["alu"], lw=0.5, z=7)


def draw_stationary(v):
    c = FILLS["cast"]
    rf, rc = L.SUCTION_FLANGE_OD / 2, 128.0
    casing = [(0, L.SUCTION_ID / 2), (0, rf), (L.SUCTION_FLANGE_T, rf), (L.SUCTION_FLANGE_T, 72),
              (78, 72), (92, 104), (108, 104), (108, rc), (L.HOUSING_X0 + 14, rc),
              (L.HOUSING_X0 + 14, 16.5), (L.D2_HUB_X, 16.5), (L.D2_HUB_X, 0),
              (L.IMP1_X0 - 12, 0), (L.IMP1_X0 - 12, L.SUCTION_ID / 2)]
    v.mirror_poly(casing, fc=c, lw=0.7, hatch="\\\\\\", z=1)
    v.mirror_poly(fluid_polygon(), fc=FILLS["fluid"], lw=0.6, z=3)
    # volute sections: top = 180 deg, bottom = 360 deg (tongue + discharge at the bottom)
    for (th, d, rcen), sgn in ((VOL[4], 1), (VOL[-1], -1)):
        v.circle((L.VOLUTE_X, sgn * rcen), d / 2 + 6, fc=c, lw=0.6, z=2)
        v.circle((L.VOLUTE_X, sgn * rcen), d / 2, fc=FILLS["fluid"], lw=0.6, z=4)
        v.rect(L.D2_SHR_X, sgn * L.R3, L.D2_HUB_X, sgn * (rcen - 0.8 * d / 2), fc=FILLS["fluid"],
               ec="none", z=4)
    # motor / bearing housing
    h0, h1, ro = L.HOUSING_X0, L.REAR_COVER[0], L.HOUSING_OD / 2
    ri = ro - L.HOUSING_WALL
    v.mirror_poly([(h0, ri), (h0, ro), (h1, ro), (h1, ri)], fc=c, lw=0.6, hatch="\\\\\\", z=1)
    for (x0, x1, bore, od) in (L.RADIAL_BRG_FRONT, L.RADIAL_BRG_REAR, *L.AXIAL_BRG):
        v.mirror_rect(x0 - 2, od / 2, x1 + 2, ri, fc=c, lw=0.5, hatch="\\\\\\", z=1)
        v.mirror_rect(x0, bore / 2 + 0.5, x1, od / 2, fc=FILLS["steel"], lw=0.5, z=4)
        v.mirror_rect(x0 + 6, bore / 2 + 10, x1 - 6, od / 2 - 12, fc=FILLS["copper"], lw=0.4, z=5)
    for (x0, x1, bore, od) in (L.TOUCHDOWN_FRONT, L.TOUCHDOWN_REAR):
        v.mirror_rect(x0 - 3, od / 2, x1 + 3, ri, fc=c, lw=0.5, hatch="\\\\\\", z=1)
        v.mirror_rect(x0, bore / 2, x1, od / 2, fc="#ffffff", lw=0.5, z=4)
        v.circle(((x0 + x1) / 2, (bore / 2 + od / 2) / 2), (od - bore) / 4 - 1, fc="#999", lw=0.3, z=5)
        v.circle(((x0 + x1) / 2, -(bore / 2 + od / 2) / 2), (od - bore) / 4 - 1, fc="#999", lw=0.3, z=5)
    sx0, sx1, sb, sod = L.STATOR
    v.mirror_rect(sx0, sb / 2, sx1, sod / 2, fc=FILLS["steel"], lw=0.6, z=4)
    v.mirror_rect(sx0 - 25, sb / 2 + 8, sx0, sod / 2 - 18, fc=FILLS["copper"], lw=0.5, z=4)
    v.mirror_rect(sx1, sb / 2 + 8, sx1 + 25, sod / 2 - 18, fc=FILLS["copper"], lw=0.5, z=4)
    v.mirror_rect(sx0 - 5, sod / 2, sx1 + 5, ri, fc=c, lw=0.5, z=1)            # stator sleeve
    for x in np.arange(sx0 + 5, sx1 - 4, L.COOLING_GROOVE_PITCH):            # cooling grooves
        v.mirror_rect(x, sod / 2 + 1, x + L.COOLING_GROOVE_W, sod / 2 + 1 + L.COOLING_GROOVE_DEPTH,
                      fc=FILLS["fluid"], lw=0.3, z=2)
    r0, r1 = L.REAR_COVER
    v.mirror_rect(r0, 12, r1, ro, fc=c, lw=0.6, hatch="\\\\\\", z=1)


def draw_externals(v, section=True):
    ex0, ex1, ez0, ez1 = L.ELECTRONICS
    v.rect(ex0, ez0, ex1, ez1, fc=FILLS["elec"], lw=0.7, z=2)
    v.rect(ex0 + 20, ez0 + 6, ex1 - 20, ez0 + 30, fc="#8fb38a", lw=0.4, z=3)          # heatsink plate
    v.text(((ex0 + ex1) / 2, ez0 + 18), "inverter + SCR heatsink plates (refrigerant cooled)", 5)
    v.text(((ex0 + ex1) / 2, ez0 + 65), "ELECTRONICS ENCLOSURE: inverter, DC-DC, bearing + motor controller, backplane", 5)
    mx0, mx1, mz0, mz1 = L.MAINS_BOX
    v.rect(mx0, mz0, mx1, mz1, fc=FILLS["elec"], lw=0.7, z=2)
    v.text(((mx0 + mx1) / 2, (mz0 + mz1) / 2), "MAINS INPUT\nBOX", 5)
    for fx0, fx1 in L.FEET:
        v.rect(fx0 - 15, -L.AXIS_HEIGHT, fx1 + 15, -L.AXIS_HEIGHT + 12, fc=FILLS["steel"], lw=0.6, z=2)
        v.rect(fx0, -L.AXIS_HEIGHT + 12, fx1, -125, fc=FILLS["cast"], lw=0.6, hatch="\\\\\\", z=0)


# ------------------------------------------------------------------ sheets
def sheet_cover(pdf):
    sh = Sheet("TC-000", "COVER SHEET & DESIGN BASIS", "-", 1, TOTAL)
    a = sh.ax
    a.text(20, 272, "TURBOCOR-CLASS TWO-STAGE MAGNETIC-BEARING CENTRIFUGAL COMPRESSOR", fontsize=14, weight="bold")
    a.text(20, 263, "Study model for SolidWorks + Ansys CFD   |   Basis: Danfoss Turbocor TTS350 as used in the "
           "Trane TCAA air-cooled chiller (IOM TCA-SVX001C-EN)", fontsize=7.5)
    c, p = DP["cycle"], DP["power"]
    rows = [("Parameter", "Value"),
            ("Refrigerant", "R-513A (R-1234yf/R-134a 56/44 wt%)"),
            ("Capacity per compressor", f"{DP['inputs']['capacity_tons']:.0f} tons ({DP['inputs']['capacity_kW']:.0f} kW)"),
            ("Sat. suction / discharge", f"{DP['inputs']['T_evap_C']:.1f} C / {DP['inputs']['T_cond_C']:.1f} C"),
            ("Suction / discharge pressure", f"{c['P_suction_kPa']:.0f} / {c['P_discharge_kPa']:.0f} kPa(a)"),
            ("Overall pressure ratio", fmt(c["PR_total"], 2)),
            ("Mass flow", f"{c['mdot_kg_s']:.2f} kg/s"),
            ("Suction volume flow", f"{c['Q_suction_m3_s']:.3f} m3/s"),
            ("Design speed", f"{DP['inputs']['speed_rpm']:,} rpm"),
            ("Shaft power / torque", f"{p['shaft_kW']:.0f} kW / {p['shaft_torque_Nm']:.1f} N.m"),
            ("Compressor kW/ton (est.)", fmt(p["kW_per_ton"], 2)),
            ("Discharge temperature", f"{c['T_discharge_C']:.0f} C"),
            ("Impeller tip dia. (both stages)", f"{S1['D2'] * 1000:.1f} mm, tip speed {S1['U2']:.0f} m/s"),
            ("Blades", DP["inputs"]["blades"] + f", backsweep {DP['inputs']['beta2b_deg']:.0f} deg"),
            ("Stage PR (1 / 2)", f"{S1['PR']:.3f} / {S2['PR']:.3f}")]
    sh.table(20, 250, rows, [60, 75], title="DESIGN POINT (from scripts/meanline.py)")
    idx = [("DWG", "Title"), ("TC-000", "Cover sheet & design basis"),
           ("TC-100/1", "General arrangement - longitudinal section"),
           ("TC-100/2", "General arrangement - exterior views"),
           ("TC-101", "Impeller, stage 1"), ("TC-102", "Impeller, stage 2"),
           ("TC-103", "Rotor shaft assembly"), ("TC-110", "Inlet housing & inlet guide vanes"),
           ("TC-120", "Compressor casing flow path, de-swirl vanes"), ("TC-121", "Volute"),
           ("TC-130", "Motor stator & housing"), ("TC-140", "Magnetic & touchdown bearings"),
           ("CFD-001", "CFD fluid domains & boundary conditions")]
    sh.table(175, 250, idx, [22, 85], title="DRAWING INDEX")
    sh.notes([
        "All dimensions mm. Coordinate system: X = rotor axis, X=0 at suction flange face, +X toward motor.",
        "Impeller/flow-path coordinates are generated - import them from cad_curves/ rather than re-typing.",
        "Geometry is a physics-based preliminary design (meanline), proportioned on Turbocor TT-class",
        "  machines. It is NOT the OEM design and must not be used for manufacture or service parts.",
        "Re-run scripts/ to change design point (speed, tonnage, refrigerant) - every sheet regenerates.",
        "Materials: impellers 7075-T6 / 2618-T61 Al; casing A356-T6 Al; shaft 17-4PH; rotor sleeve CFRP;",
        "  laminations M270-35A / Co-Fe for bearings; housing A356-T6 / ductile iron.",
    ], x=20, y=178, size=6.3)
    sh.save(pdf, OUT / "TC-000.png")


def sheet_ga_section(pdf):
    sh = Sheet("TC-100/1", "GENERAL ARRANGEMENT - SECTION", "1:3", 2, TOTAL)
    v = sh.view(28, 135, 1 / 3)
    draw_externals(v)
    draw_stationary(v)
    draw_rotor(v)
    v.centerline((-8, 0), (L.LENGTH + 8, 0))
    # overall dims
    v.dim((0, -L.AXIS_HEIGHT), (L.LENGTH, -L.AXIS_HEIGHT), -7, orient="h")
    v.dim((L.LENGTH, -L.AXIS_HEIGHT), (L.LENGTH, L.ELECTRONICS[3]), 6, orient="v")
    v.dim((0, 0), (0, -L.AXIS_HEIGHT), -6, orient="v")
    v.dim((L.IMP1_X0, 140), (L.IMP2_X0, 140), 10, orient="h", fmt="{:.0f}")
    v.dim((0, 140), (L.IMP1_X0, 140), 10, orient="h", fmt="{:.0f}")
    v.dim((L.ROTOR_X0, -175), (L.ROTOR_X1, -175), 0.1, orient="h", text=f"ROTOR {L.ROTOR_X1 - L.ROTOR_X0:.0f}")
    items = [
        (1, (10, 80), (10, 210), "Suction flange DN100"),
        (2, (L.IGV_X + 10, 30), (40, 245), "Inlet guide vanes (8)"),
        (3, (L.IMP1_X0 + 15, 35), (95, 250), "Impeller stage 1"),
        (4, (L.RC_SHR_X + 4, 60), (150, 255), "De-swirl / return channel"),
        (5, (L.IMP2_X0 + 15, 35), (205, 250), "Impeller stage 2"),
        (6, (L.VOLUTE_X, 94), (245, 245), "Volute"),
        (7, (255, 60), (300, 255), "Front radial mag. bearing"),
        (8, (215, 22), (265, 230), "Touchdown bearing (front)"),
        (9, (380, 100), (380, 250), "Motor stator (cooling grooves)"),
        (10, (380, 30), (430, 250), "PM rotor, CFRP sleeve"),
        (11, (520, 60), (520, 250), "Rear radial mag. bearing"),
        (12, (575, 55), (580, 245), "Axial (thrust) bearing"),
        (13, (630, 9), (650, 235), "Axial sensor / rear touchdown"),
        (14, (450, 220), (470, 300), "Electronics enclosure"),
        (15, (730, 50), (760, 230), "Mains input box"),
        (16, (160, -195), (110, -235), "Mounting feet"),
    ]
    for n, p, q, _ in items:
        v.balloon(p, q, n)
    rows = [("#", "Component")] + [(n, name) for n, _, _, name in items]
    sh.table(330, 280, rows, [6, 68], title="ITEM LIST", size=5.3, row_h=3.8)
    sh.text(28, 52, "Section through rotor axis. Volute shown at 180 deg (top) and 360 deg (bottom). "
            "Gas: suction -> IGV -> stage 1 -> diffuser -> crossover -> de-swirl vanes -> stage 2 -> volute.",
            fontsize=5.8)
    sh.text(28, 48, "Motor cooling (IOM): liquid R-513A -> solenoids/orifices -> inverter & SCR heatsinks -> "
            "stator grooves -> vapour returns to suction through motor cavity.", fontsize=5.8)
    sh.save(pdf, OUT / "TC-100-1.png")


def sheet_ga_exterior(pdf):
    sh = Sheet("TC-100/2", "GENERAL ARRANGEMENT - EXTERIOR", "1:6", 3, TOTAL)
    s = 1 / 6
    # side elevation (looking along -Y)
    v = sh.view(30, 205, s, "SIDE ELEVATION  1:6", label_xy=(96, 264))
    ex0, ex1, ez0, ez1 = L.ELECTRONICS
    rf = L.SUCTION_FLANGE_OD / 2
    v.rect(0, -rf, L.SUCTION_FLANGE_T, rf, fc=FILLS["cast"])
    v.rect(L.SUCTION_FLANGE_T, -72, 92, 72, fc=FILLS["cast"])
    v.rect(92, -128, L.HOUSING_X0 + 14, 128, fc=FILLS["cast"])
    v.rect(L.HOUSING_X0 + 14, -150, L.REAR_COVER[1], 150, fc=FILLS["cast"])
    draw_externals(v)
    vz = -VOL[-1][2]                    # discharge leaves the volute at the bottom, toward +Y
    v.circle((L.VOLUTE_X, vz), L.DISCHARGE_FLANGE_OD / 2, fc=FILLS["steel"], z=4)
    v.circle((L.VOLUTE_X, vz), L.DISCHARGE_ID / 2, fc="white", z=5)
    v.centerline((-5, 0), (L.LENGTH + 5, 0))
    v.dim((0, -L.AXIS_HEIGHT), (L.LENGTH, -L.AXIS_HEIGHT), -5)
    v.dim((L.LENGTH, -L.AXIS_HEIGHT), (L.LENGTH, ez1), 5, orient="v")
    v.dim((0, rf), (L.VOLUTE_X, rf), 22, fmt="{:.0f}")
    v.dim((ex0, ez1), (ex1, ez1), 6, fmt="{:.0f}")
    v.dim((0, 0), (0, -L.AXIS_HEIGHT), -6, orient="v")
    v.dim((L.VOLUTE_X, vz), (L.VOLUTE_X, 0), -18, orient="v")
    for fx0, fx1 in L.FEET:
        v.dim((fx0, -L.AXIS_HEIGHT), (fx1, -L.AXIS_HEIGHT), -12, fmt="{:.0f}")
    # top view (looking down -Z): Y up on paper
    t = sh.view(30, 105, s, "PLAN  1:6", label_xy=(96, 50))
    t.rect(0, -rf, L.SUCTION_FLANGE_T, rf, fc=FILLS["cast"])
    t.rect(L.SUCTION_FLANGE_T, -72, 92, 72, fc=FILLS["cast"])
    t.rect(92, -128, L.HOUSING_X0 + 14, 128, fc=FILLS["cast"])
    t.rect(ex0, -L.WIDTH / 2, ex1, L.WIDTH / 2, fc=FILLS["elec"], z=3)
    t.rect(L.MAINS_BOX[0], -120, L.MAINS_BOX[1], 120, fc=FILLS["elec"], z=3)
    dy = 230.0
    t.rect(L.VOLUTE_X - L.DISCHARGE_ID / 2 - 6, 100, L.VOLUTE_X + L.DISCHARGE_ID / 2 + 6, dy, fc=FILLS["cast"], z=4)
    t.rect(L.VOLUTE_X - L.DISCHARGE_FLANGE_OD / 2, dy, L.VOLUTE_X + L.DISCHARGE_FLANGE_OD / 2,
           dy + L.DISCHARGE_FLANGE_T, fc=FILLS["steel"], z=4)
    t.text((L.VOLUTE_X + 95, dy + 10), "DISCHARGE DN50", 5)
    t.text((40, 0), "SUCTION\nDN100", 5)
    t.centerline((-5, 0), (L.LENGTH + 5, 0))
    t.dim((L.LENGTH, -L.WIDTH / 2), (L.LENGTH, L.WIDTH / 2), 5, orient="v")
    t.dim((L.VOLUTE_X, 0), (L.VOLUTE_X, dy + L.DISCHARGE_FLANGE_T), -40, orient="v")
    for fx0, fx1 in L.FEET:
        for yy in (-L.FOOT_SPAN / 2, L.FOOT_SPAN / 2):
            t.circle(((fx0 + fx1) / 2, yy), 7, ls="--", lw=0.5, z=5)
    t.dim(((L.FEET[0][0] + L.FEET[0][1]) / 2, -L.FOOT_SPAN / 2), ((L.FEET[1][0] + L.FEET[1][1]) / 2, -L.FOOT_SPAN / 2), -12, fmt="{:.0f}")
    t.text((360, -L.FOOT_SPAN / 2 + 25), f"4x Ø14 THRU, {L.FOOT_SPAN:.0f} SPAN", 5)
    # end view from suction
    e = sh.view(305, 205, s, "END VIEW FROM SUCTION  1:6  (+Y to the left)", label_xy=(305, 158))
    e.rect(-L.WIDTH / 2, ez0, L.WIDTH / 2, ez1, fc=FILLS["elec"])
    e.circle((0, 0), 150, fc=FILLS["cast"])
    e.circle((0, 0), 128, fc=FILLS["cast"])
    e.circle((0, 0), rf, fc=FILLS["steel"])
    e.circle((0, 0), L.SUCTION_ID / 2, fc="white")
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        e.circle((90 * math.cos(a), 90 * math.sin(a)), 9, fc="white", lw=0.5)
    # viewed from suction, +Y points to the LEFT of the paper
    e.rect(-100, vz - L.DISCHARGE_ID / 2 - 6, -dy, vz + L.DISCHARGE_ID / 2 + 6, fc=FILLS["cast"])
    e.rect(-dy, vz - L.DISCHARGE_FLANGE_OD / 2, -dy - L.DISCHARGE_FLANGE_T, vz + L.DISCHARGE_FLANGE_OD / 2, fc=FILLS["steel"])
    e.rect(-L.FOOT_SPAN / 2 - 20, -L.AXIS_HEIGHT, L.FOOT_SPAN / 2 + 20, -L.AXIS_HEIGHT + 12, fc=FILLS["steel"])
    e.rect(-60, -L.AXIS_HEIGHT + 12, 60, -125, fc=FILLS["cast"])
    e.center_mark((0, 0), 120)
    e.dim((-L.WIDTH / 2, ez1), (L.WIDTH / 2, ez1), 5)
    e.dia((0, 0), L.SUCTION_ID / 2, 300, text="Ø102 ID (DN100)", out=40)
    e.dia((0, 0), rf, 60, text=f"Ø{2 * rf:.0f} FLANGE, 8x Ø18 PCD 180", out=14)
    e.dim((-L.FOOT_SPAN / 2, -L.AXIS_HEIGHT), (L.FOOT_SPAN / 2, -L.AXIS_HEIGHT), -6, fmt="{:.0f}")
    sh.notes(["Envelope ~790 x 480 x 465 mm matches published Turbocor TT-class dimensions.",
              "Flange sizes from flow velocity: suction ~22 m/s, discharge ~21 m/s.",
              "Electronics/mains boxes are simple sheet-metal shells - model as thin-wall parts.",
              "CFD does not need the externals; suppress them in a 'CFD' configuration."],
             x=190, y=140, size=5.8)
    sh.save(pdf, OUT / "TC-100-2.png")


def sheet_impeller(pdf, stage):
    s = S1 if stage == 1 else S2
    x0 = L.IMP1_X0 if stage == 1 else L.IMP2_X0
    sh = Sheet(f"TC-10{stage}", f"IMPELLER - STAGE {stage}", "2.5:1 / 0.9:1", 3 + stage, TOTAL,
               material="7075-T6 aluminium (or 2618-T61), balance G1.0, overspeed 115%")
    v = sh.view(72 - 2.5 * x0, 110, 2.5, "MERIDIONAL HALF-SECTION  2.5:1", label_xy=(115, 98))
    hub = FP["hub1"] if stage == 1 else FP["hub2"]
    shr = FP["imp_shr1"] if stage == 1 else FP["imp_shr2"]
    v.poly(blade_region(stage), fc=FILLS["blade"], lw=0.6)
    v.poly(impeller_body(stage, x0), fc=FILLS["alu"], hatch="////", lw=0.8)
    v.line(shr, lw=0.9)
    v.centerline((x0 - 6, 0), (x0 + L.IMP_L + 10, 0))
    r1h, r1t, r2, b2 = hub[0, 1], shr[0, 1], L.R2, s["b2"] * 1000
    xb = x0 + L.IMP_L + L.BACKPLATE_T
    v.dim((x0, 0), (x0, r1h), -6, orient="v", text=f"Ø{2 * r1h:.1f}")
    v.dim((x0, 0), (x0, r1t), -14, orient="v", text=f"Ø{2 * r1t:.1f} EYE")
    v.dim((xb, 0), (xb, r2), 22, orient="v", text=f"Ø{2 * r2:.1f} TIP")
    v.dim((xb, 0), (xb, L.SHAFT_D_IMP / 2), 8, orient="v", text=f"Ø{L.SHAFT_D_IMP:.0f} H7 BORE")
    v.dim((x0, r2), (x0 + L.IMP_L, r2), 8)
    v.dim((x0 + L.IMP_L, r2), (xb, r2), 16, text=f"{L.BACKPLATE_T:.1f}")
    v.dim((x0, r1t), (shr[-1, 0], r1t), 5)
    v.dim((shr[-1, 0], r2), (x0 + L.IMP_L, r2), 4, text=f"b2={b2:.2f}", orient="h")
    v.leader((shr[len(shr) // 2, 0], shr[len(shr) // 2, 1]), (x0 + 2, r2 + 4), "SHROUD LINE (open impeller,\n"
             f"{L.TIP_CLEARANCE} mm running clearance)")
    v.leader((hub[30, 0], hub[30, 1] - 1), (x0 + L.IMP_L + 8, r1h + 4), "HUB LINE")
    v.text((x0 + 10, r1h + 10), "BLADE", 6)
    # blade table
    tab = np.loadtxt(L.ROOT / "cad_curves" / f"stage{stage}" / "impeller_table.csv", delimiter=",", skiprows=1)
    rows = [("m", "hub z", "hub r", "hub β", "hub θ", "shr z", "shr r", "shr β", "shr θ")]
    for k in (0, 5, 10, 15, 20, 25, 30, 35, 40):
        rows.append(tuple(f"{tab[k, j]:.2f}" if j == 0 else f"{tab[k, j]:.1f}" for j in range(9)))
    sh.table(186, 270, rows, [10, 12, 12, 11, 12, 12, 12, 11, 12],
             title="BLADE DEFINITION (local z from eye, mm; β from meridional, θ wrap, deg)", size=5.2, row_h=4.0)
    key = [("Feature", "Value"),
           ("Main blades / splitters", f"{DP['inputs']['blades']}"),
           ("Splitter LE at", "30 % meridional length"),
           ("Blade thickness hub / shroud", "2.0 / 1.0 mm, LE elliptical 2:1"),
           ("Exit blade angle β2b", f"{DP['inputs']['beta2b_deg']:.0f} deg backswept"),
           ("Inlet relative Mach (tip)", fmt(s["M1rel"], 2)),
           ("Tip speed U2", f"{s['U2']:.0f} m/s @ {DP['inputs']['speed_rpm']:,} rpm"),
           ("Stage pressure ratio", fmt(s["PR"], 3)),
           ("Fillets", "R1.0 hub, blade tips sharp"),
           ("Curve files", f"cad_curves/stage{stage}/*.txt")]
    sh.table(186, 222, key, [44, 60], title="KEY DATA", size=5.4, row_h=4.0)
    # front view
    fv = sh.view(355, 185, 0.9, "VIEW FROM INLET  0.9:1", label_xy=(355, 120))
    d = L.ROOT / "cad_curves" / f"stage{stage}"
    mh, ms = np.loadtxt(d / "main_hub_camber.txt"), np.loadtxt(d / "main_shroud_camber.txt")
    sp_h, sp_s = np.loadtxt(d / "splitter_hub_camber.txt"), np.loadtxt(d / "splitter_shroud_camber.txt")
    fv.circle((0, 0), r2, fc=FILLS["alu"], lw=0.9)
    fv.circle((0, 0), r1t, ls="--", lw=0.5)
    fv.circle((0, 0), r1h, fc="#f4f4f4", lw=0.6)
    fv.circle((0, 0), L.SHAFT_D_IMP / 2, fc="white", lw=0.6)
    pitch = 2 * math.pi / 7
    for k in range(7):
        c, si = math.cos(k * pitch), math.sin(k * pitch)
        rot = lambda p: np.column_stack([-(p[:, 0] * c - p[:, 1] * si), p[:, 0] * si + p[:, 1] * c])
        fv.line(rot(mh), lw=1.1)
        fv.line(rot(ms), lw=0.5, c="#666")
        fv.line(rot(sp_h), lw=0.9, c="#8a5a00")
    fv.center_mark((0, 0), r2 + 6)
    fv.dia((0, 0), r2, 35)
    fv.dia((0, 0), r1t, 150, out=22)
    fv.text((0, -r2 - 12), "ROTATION: CW VIEWED FROM INLET  (+X right-hand)", 5.2)
    fv.text((0, r2 + 10), "black = main hub camber, grey = main shroud camber,\nbrown = splitter hub camber", 5)
    sh.notes([f"Machine from solid. Place eye plane at X = {x0:.1f} in the assembly.",
              "Blade = Boundary Surface between hub & shroud camber curves, Thicken 1.5 mm midplane.",
              "Extend blade surfaces 1 mm past hub/shroud before Thicken, then trim (see guide).",
              "Pattern blade 7x about axis; splitter pattern 7x offset by 25.71 deg.",
              "Back face flat; balance holes optional. Tie-bolt clamps both impellers + spacer."],
             x=14, y=82, size=5.6)
    sh.save(pdf, OUT / f"TC-10{stage}.png")


def sheet_shaft(pdf):
    sh = Sheet("TC-103", "ROTOR SHAFT ASSEMBLY", "1:2", 6, TOTAL,
               material="17-4PH H1025 shaft; CFRP magnet sleeve; Si-steel/Co-Fe bearing laminations")
    v = sh.view(30 - L.ROTOR_X0 / 2, 175, 0.5, "ROTOR ELEVATION  1:2", label_xy=(160, 222))
    draw_rotor(v)
    v.centerline((L.ROTOR_X0 - 10, 0), (L.ROTOR_X1 + 10, 0))
    prev = None
    for i, (x0, x1, d, name) in enumerate(L.SHAFT):
        v.dim((x0, d / 2), (x0, -d / 2), -2 - (i % 2) * 0 if False else -1.5, orient="v",
              text=f"Ø{d:.0f}", size=4.6) if d >= 40 else None
    for i, (x0, x1, d, name) in enumerate(L.SHAFT):
        v.dim((x0, -60), (x1, -60), -6 - 6 * (i % 3), fmt="{:.0f}", size=4.6)
    v.dim((L.ROTOR_X0, 60), (L.ROTOR_X1, 60), 10, fmt="{:.0f}")
    rows = [("Seg", "X from", "X to", "Ø", "Function")]
    for i, (x0, x1, d, name) in enumerate(L.SHAFT, 1):
        rows.append((i, f"{x0:.1f}", f"{x1:.1f}", f"{d:.0f}", name))
    t0, t1, od = L.THRUST_DISK
    rows.append(("TD", f"{t0:.0f}", f"{t1:.0f}", f"{od:.0f}", "thrust disk (shrink fit, 17-4PH / Co-Fe)"))
    sh.table(20, 120, rows, [9, 15, 15, 9, 75], title="SEGMENT TABLE (X in machine coordinates)", size=5.2, row_h=4.0)
    rotor_mass = sum(math.pi / 4 * (d / 1000) ** 2 * (x1 - x0) / 1000 * 7800 for x0, x1, d, _ in L.SHAFT)
    sh.notes([f"Estimated rotor mass ~{rotor_mass + 0.6:.1f} kg (steel est. + 2 Al impellers).",
              "Model as ONE revolved part from the segment table, then split bodies for colour.",
              "Impellers, spacer sleeve & nose nut clamped by an M10 tie-bolt (not shown).",
              "Motor: 2-pole surface PM, Sm2Co17 magnets, 5 mm CFRP sleeve (tip speed ~110 m/s).",
              "Radial air gap at mag-bearing journals 0.5 mm; touchdown clearance 0.2 mm radial.",
              "First bending critical must stay >20% above 39,000 rpm max - check in Ansys Modal."],
             x=170, y=118, size=5.6)
    sh.save(pdf, OUT / "TC-103.png")


def naca0012(c, n=40):
    x = (1 - np.cos(np.linspace(0, math.pi, n))) / 2
    yt = 0.6 * (0.2969 * np.sqrt(x) - 0.126 * x - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1036 * x ** 4)
    return np.vstack([np.column_stack([x * c, yt * c]), np.column_stack([x[::-1] * c, -yt[::-1] * c])])


def sheet_igv(pdf):
    sh = Sheet("TC-110", "INLET HOUSING & INLET GUIDE VANES", "1:1.5 / 3:4 / 2:1", 7, TOTAL,
               material="Housing A356-T6; vanes 6061-T6; pivot pins 316 SS w/ PTFE bushes")
    v = sh.view(35, 165, 1 / 1.5, "INLET SECTION  1:1.5", label_xy=(70, 76))
    rf = L.SUCTION_FLANGE_OD / 2
    outline = [(0, L.SUCTION_ID / 2), (0, rf), (L.SUCTION_FLANGE_T, rf), (L.SUCTION_FLANGE_T, 72),
               (78, 72), (92, 104), (L.IMP1_X0, 104)]
    shr = FP["inlet_shr"]
    poly = np.vstack([outline, shr[::-1]])
    v.mirror_poly(poly, fc=FILLS["cast"], hatch="\\\\\\")
    for sgn in (1, -1):
        v.rect(L.IGV_X - 0.25 * L.IGV_CHORD, sgn * 6, L.IGV_X + 0.75 * L.IGV_CHORD, sgn * L.SUCTION_ID / 2,
               fc="#9aa", lw=0.5, alpha=0.6)
        v.line([(L.IGV_X, sgn * L.SUCTION_ID / 2), (L.IGV_X, sgn * 80)], lw=1.0)
    v.centerline((-5, 0), (105, 0))
    v.dim((0, rf), (L.SUCTION_FLANGE_T, rf), 5, fmt="{:.0f}")
    v.dim((0, L.SUCTION_ID / 2), (0, -L.SUCTION_ID / 2), -8, orient="v", text=f"Ø{L.SUCTION_ID:.0f}")
    v.dim((0, rf), (0, -rf), -16, orient="v", text=f"Ø{2 * rf:.0f}")
    v.dim((0, -rf), (L.IGV_X, -rf), -5, fmt="{:.0f}", text=f"{L.IGV_X:.0f} (pivot)")
    v.dim((0, -rf), (L.IMP1_X0, -rf), -12, fmt="{:.0f}", text=f"{L.IMP1_X0:.0f} (eye plane)")
    v.dim((L.IMP1_X0, shr[-1, 1]), (L.IMP1_X0, -shr[-1, 1]), 10, orient="v", text=f"Ø{2 * shr[-1, 1]:.1f}")
    v.text((L.IGV_X + 5, 3), "IGV (projected, open)", 5)
    # IGV face view
    f = sh.view(215, 170, 0.75, "IGV ASSEMBLY - VIEW FROM SUCTION  3:4  (vanes at 0° = fully open)", label_xy=(215, 98))
    f.circle((0, 0), L.SUCTION_ID / 2, fc=FILLS["fluid"])
    f.circle((0, 0), 72, lw=0.6)
    f.circle((0, 0), 85, lw=0.5, ls="--")
    for k in range(L.IGV_COUNT):
        a = 2 * math.pi * k / L.IGV_COUNT
        ca, sa = math.cos(a), math.sin(a)
        r0, r1 = 6.0, L.SUCTION_ID / 2
        w = L.IGV_CHORD * 0.12 / 2
        pts = [(r0, -w), (r1, -w), (r1, w), (r0, w)]
        f.poly([(x * ca - y * sa, x * sa + y * ca) for x, y in pts], fc="#9aa", lw=0.5, z=4)
        f.circle((78 * ca, 78 * sa), 3, fc="white", lw=0.5, z=4)
        f.line([(r1 * ca, r1 * sa), (85 * ca, 85 * sa)], lw=0.8)
    f.center_mark((0, 0), 90)
    f.dia((0, 0), 72, 20, text="Ø144 HOUSING", out=12)
    f.dia((0, 0), 85, 60, text="Ø170 SYNC RING", out=12)
    # vane detail
    dv = sh.view(335, 85, 2.0, "VANE SECTION NACA 0012, chord 40  2:1", label_xy=(345, 106))
    dv.poly(naca0012(L.IGV_CHORD) - [L.IGV_CHORD * 0.25, 0], fc="#9aa")
    dv.circle((0, 0), 1.5, fc="white")
    dv.dim((-L.IGV_CHORD * 0.25, 4), (L.IGV_CHORD * 0.75, 4), 6, fmt="{:.0f}")
    dv.dim((-L.IGV_CHORD * 0.25, -4), (0, -4), -6, text="10 (pivot @ 25% c)")
    sh.notes([f"{L.IGV_COUNT} cantilevered vanes, span r = 6 to {L.SUCTION_ID / 2:.0f} mm, pivot pin Ø6 through housing wall.",
              "Range 0 deg (open) to 70 deg closed; prewhirl in rotation direction reduces capacity.",
              "For CFD at design point model IGVs at 0 deg or omit them (they are a pressure-drop item).",
              "Inlet contraction to the eye: use cad_curves/flowpath_shroud.txt (spline)."],
             x=14, y=62, size=5.6)
    sh.save(pdf, OUT / "TC-110.png")


def sheet_casing(pdf):
    sh = Sheet("TC-120", "COMPRESSOR CASING FLOW PATH & DE-SWIRL VANES", "1:1 / 1:2", 8, TOTAL,
               material="A356-T6 casting (split: inlet/shroud casing, diaphragm, volute casing)")
    v = sh.view(25, 105, 1.0, "MERIDIONAL FLOW PATH (upper half)  1:1", label_xy=(100, 95))
    v.poly(fluid_polygon(), fc=FILLS["fluid"], lw=0.8)
    v.poly(blade_region(1), fc=FILLS["blade"], lw=0.4)
    v.poly(blade_region(2), fc=FILLS["blade"], lw=0.4)
    v.centerline((-5, 0), (L.VOLUTE_X + 30, 0))
    th, d, rc = VOL[-1]
    v.circle((L.VOLUTE_X, rc), d / 2, fc=FILLS["fluid"], lw=0.8)
    v.rect(L.D2_SHR_X, L.R3, L.D2_HUB_X, rc - 0.8 * d / 2, fc=FILLS["fluid"], ec="none", z=4)
    v.dim((L.IMP1_X0, L.R3 + 15), (L.IMP2_X0, L.R3 + 15), 4, fmt="{:.1f}")
    v.dim((0, L.R3 + 15), (L.IMP1_X0, L.R3 + 15), 4, fmt="{:.1f}")
    v.dim((L.D1_SHR_X, L.R3), (L.D1_HUB_X, L.R3), -18, text=f"b3={L.B3_1:.2f}")
    v.dim((L.RC_SHR_X, L.R3), (L.RC_HUB_X, L.R3), -18, text=f"{L.B3_1:.2f}")
    v.dim((L.D1_HUB_X, 45), (L.RC_SHR_X, 45), 0.1, text=f"{L.CROSSOVER_GAP:.0f}")
    v.dim((L.D1_HUB_X - 30, 0), (L.D1_HUB_X - 30, L.R3), 0.1, orient="v", text=f"R3={L.R3:.1f}")
    v.dim((L.D1_HUB_X - 22, 0), (L.D1_HUB_X - 22, L.R2), 0.1, orient="v", text=f"R2={L.R2:.2f}")
    v.dim((L.VOLUTE_X + 25, 0), (L.VOLUTE_X + 25, rc), 0.1, orient="v", text=f"Rc={rc:.1f}")
    v.leader((L.BEND_CX, L.R3 + L.BEND_R_OUT), (L.BEND_CX - 40, L.R3 + 30),
             f"CROSSOVER BEND R{L.BEND_R_IN:.2f} / R{L.BEND_R_OUT:.2f}")
    v.leader((L.RC_SHR_X + 3, 60), (L.RC_SHR_X + 30, 72), f"DE-SWIRL VANES ({L.DESWIRL_COUNT})")
    v.leader((L.VOLUTE_X, rc + d / 2), (L.VOLUTE_X - 30, rc + d / 2 + 12), "VOLUTE @ 360°")
    rows = [("Plane", "X", "r hub", "r shroud")]
    for name, x, rh, rs in [
        ("Suction flange", 0, 0, L.SUCTION_ID / 2),
        ("IGV pivot", L.IGV_X, 0, L.SUCTION_ID / 2),
        ("Eye 1", L.IMP1_X0, FP["hub1"][0, 1], FP["shr1"][0, 1]),
        ("Diffuser 1 in", f"{L.D1_SHR_X:.2f}-{L.D1_HUB_X:.2f}", L.R2, L.R2),
        ("Diffuser 1 out", f"{L.D1_SHR_X:.2f}-{L.D1_HUB_X:.2f}", L.R3, L.R3),
        ("Return ch. in", f"{L.RC_SHR_X:.2f}-{L.RC_HUB_X:.2f}", L.R3, L.R3),
        ("Eye 2", L.IMP2_X0, FP["hub2"][0, 1], FP["shr2"][0, 1]),
        ("Diffuser 2 out", f"{L.D2_SHR_X:.2f}-{L.D2_HUB_X:.2f}", L.R3, L.R3)]:
        rows.append((name, x if isinstance(x, str) else f"{x:.1f}", f"{rh:.2f}", f"{rs:.2f}"))
    sh.table(275, 280, rows, [30, 30, 18, 18], title="FLOW-PATH STATIONS (mm)", size=5.2, row_h=4.0)
    # de-swirl vane cascade (plan view, r-theta)
    dv = sh.view(335, 180, 0.5, "DE-SWIRL VANES - plan  1:2", label_xy=(335, 128))
    dv.circle((0, 0), L.R3, lw=0.5, ls="--")
    dv.circle((0, 0), L.RC_INNER_R, lw=0.5, ls="--")
    a_in = math.radians(DESWIRL_IN)
    rr = np.linspace(L.R3, L.RC_INNER_R, 30)
    frac = (L.R3 - rr) / (L.R3 - L.RC_INNER_R)
    beta = a_in * (1 - frac) ** 1.5                      # angle from radial, -> 0 at exit
    dth = np.concatenate([[0], np.cumsum(-np.tan(0.5 * (beta[1:] + beta[:-1])) * np.diff(rr) / rr[1:])])
    for k in range(L.DESWIRL_COUNT):
        ph = 2 * math.pi * k / L.DESWIRL_COUNT
        th = ph - dth
        dv.line(np.column_stack([rr * np.cos(th), rr * np.sin(th)]), lw=1.2)
    dv.center_mark((0, 0), L.R3 + 5)
    sh.table(275, 120, [("De-swirl vane", "Value"), ("Count", L.DESWIRL_COUNT),
                       ("Inlet r / metal angle", f"{L.R3:.1f} / {DESWIRL_IN:.1f}° from radial"),
                       ("Exit r / metal angle", f"{L.RC_INNER_R:.0f} / 0° (no swirl)"),
                       ("Thickness", "3 mm, round LE, sharp TE"),
                       ("Camber law", "β = β_in (1-f)^1.5")], [32, 55], size=5.2, row_h=4.0)
    sh.notes(["Flow path walls exported as cad_curves/flowpath_*.txt (X r 0) - use Curve Through XYZ",
              "  Points on the Front plane, then Revolve about the X axis.",
              "Split the casting at diffuser-1 hub wall (diaphragm) & diffuser-2 hub wall (bearing housing).",
              "Diaphragm is held by the de-swirl vanes; it carries the interstage labyrinth at Ø26."],
             x=14, y=60, size=5.6)
    sh.save(pdf, OUT / "TC-120.png")


def sheet_volute(pdf):
    sh = Sheet("TC-121", "VOLUTE", "0.6:1", 9, TOTAL, material="A356-T6, integral with stage-2 casing")
    v = sh.view(150, 175, 0.6, "VOLUTE PLAN, VIEW FROM INLET  0.6:1", label_xy=(150, 92))
    th = np.linspace(0, 360, 73)
    secs = np.array([[t, d, rc] for t, d, rc in VOL])
    dd = np.interp(th, secs[:, 0], secs[:, 1])
    rcc = np.interp(th, secs[:, 0], secs[:, 2])
    a = np.radians(270.0 - th)          # screen angle: θ runs clockwise, θ=360 at 6 o'clock
    outer = rcc + dd / 2
    v.circle((0, 0), L.R3, lw=0.6, ls="--")
    v.circle((0, 0), L.R2, lw=0.5, ls=":")
    v.line(np.column_stack([outer * np.cos(a), outer * np.sin(a)]), lw=1.1)
    v.line(np.column_stack([rcc * np.cos(a), rcc * np.sin(a)]), lw=0.4, c="#888", ls="--")
    # discharge cone tangent at 360 deg
    r_end, d_end = rcc[-1], dd[-1]
    cone_len = 140.0
    p0 = np.array([0.0, -r_end])
    tan = np.array([-1.0, 0.0])          # CW tangent at 6 o'clock = paper left = +Y
    nrm = np.array([0.0, -1.0])
    q0a, q0b = p0 + nrm * d_end / 2, p0 - nrm * d_end / 2
    p1 = p0 + tan * cone_len
    q1a, q1b = p1 + nrm * L.DISCHARGE_ID / 2, p1 - nrm * L.DISCHARGE_ID / 2
    v.line([q0a, q1a], lw=1.0)
    v.line([q0b, q1b], lw=1.0)
    v.line([p1 + nrm * L.DISCHARGE_FLANGE_OD / 2, p1 - nrm * L.DISCHARGE_FLANGE_OD / 2], lw=2.0)
    v.dim(tuple(p0 + nrm * 45), tuple(p1 + nrm * 45), -3, orient="h", text=f"{cone_len:.0f} cone, 2·{math.degrees(math.atan((L.DISCHARGE_ID - d_end) / 2 / cone_len)):.1f}°")
    v.text((p1[0] + 5, p1[1] + 50), "DISCHARGE DN50\n(+Y)", 5.5)
    for t, d, rc in VOL[1:]:
        ang = math.radians(270.0 - t)
        v.line([(L.R3 * math.cos(ang), L.R3 * math.sin(ang)), ((rc + d / 2) * math.cos(ang), (rc + d / 2) * math.sin(ang))], lw=0.4, c="#888")
        v.text(((rc + d / 2 + 9) * math.cos(ang), (rc + d / 2 + 9) * math.sin(ang)), f"{t:.0f}°", 5)
    v.center_mark((0, 0), 115)
    v.text((0, -20), "θ = 0° at tongue (6 o'clock),\nincreasing clockwise = with rotation", 5)
    rows = [("θ deg", "Ø section", "Rc", "Area mm²")]
    for t, d, rc in VOL:
        rows.append((f"{t:.0f}", f"{d:.1f}", f"{rc:.1f}", f"{math.pi * d * d / 4:.0f}"))
    sh.table(270, 270, rows, [18, 20, 18, 22], title="VOLUTE SECTIONS (circular, external)", size=5.4, row_h=4.2)
    sh.notes(["Sizing: constant angular momentum, A(θ)/Rc = Q·θ / (2π·Cθ2·R2).",
              f"Q at volute = {VOL_Q * 1000:.1f} L/s, Cθ2 = {S2['Ct2']:.0f} m/s at R2 = {L.R2:.1f} mm.",
              "Model: Sweep a circle along the Rc spiral with a guide curve on the outer edge, OR",
              "  Loft through the 9 circular sections (planes every 45°) - easier in SolidWorks.",
              "Tongue clearance 5% of R3. Section plane = through rotor axis.",
              f"Volute axial centre X = {L.VOLUTE_X:.2f} (mid-width of diffuser 2)."],
             x=255, y=225, size=5.6)
    sh.save(pdf, OUT / "TC-121.png")


def sheet_motor(pdf):
    sh = Sheet("TC-130", "MOTOR STATOR & HOUSING", "1:3 / 1:2", 10, TOTAL,
               material="Housing A356-T6 / ductile iron; stator 0.2 mm NO20 laminations; Cu Litz windings")
    v = sh.view(25 - L.HOUSING_X0 / 3, 160, 1 / 3, "HOUSING SECTION 1:3", label_xy=(100, 92))
    h0, h1, ro = L.HOUSING_X0, L.REAR_COVER[0], L.HOUSING_OD / 2
    ri = ro - L.HOUSING_WALL
    sx0, sx1, sb, sod = L.STATOR
    v.mirror_poly([(h0, ri), (h0, ro), (h1, ro), (h1, ri)], fc=FILLS["cast"], hatch="\\\\\\")
    v.mirror_rect(sx0 - 5, sod / 2, sx1 + 5, ri, fc=FILLS["cast"])
    for x in np.arange(sx0 + 5, sx1 - 4, L.COOLING_GROOVE_PITCH):
        v.mirror_rect(x, sod / 2 + 1, x + L.COOLING_GROOVE_W, sod / 2 + 1 + L.COOLING_GROOVE_DEPTH, fc=FILLS["fluid"], lw=0.3)
    v.mirror_rect(sx0, sb / 2, sx1, sod / 2, fc=FILLS["steel"])
    v.mirror_rect(sx0 - 25, sb / 2 + 8, sx0, sod / 2 - 18, fc=FILLS["copper"])
    v.mirror_rect(sx1, sb / 2 + 8, sx1 + 25, sod / 2 - 18, fc=FILLS["copper"])
    v.centerline((h0 - 10, 0), (h1 + 25, 0))
    v.dim((h0, ro), (h1, ro), 6, fmt="{:.1f}")
    v.dim((sx0, -sod / 2), (sx1, -sod / 2), -18, fmt="{:.0f}", text=f"{sx1 - sx0:.0f} STACK")
    v.dim((h0, 0), (h0, ro), -4, orient="v", text=f"Ø{2 * ro:.0f}")
    v.dim((sx1 + 30, 0), (sx1 + 30, sod / 2), 0.1, orient="v", text=f"Ø{sod:.0f}")
    v.dim((sx1 + 45, 0), (sx1 + 45, sb / 2), 0.1, orient="v", text=f"Ø{sb:.0f}")
    v.dim((0 + 260, ri), (260, ro), 0.1, orient="v", text=f"{L.HOUSING_WALL:.0f}")
    v.text((sx1 - 20, ro + 14), "liquid-injection inlet (from orifices) at stator-sleeve groove start", 5)
    v.leader((sx0 + 12, -sod / 2 - 3), (sx0 - 60, -ro - 25), f"Helical cooling groove {L.COOLING_GROOVE_W:.0f}w x {L.COOLING_GROOVE_DEPTH:.0f}d, pitch {L.COOLING_GROOVE_PITCH:.0f}")
    # stator lamination end view
    e = sh.view(320, 175, 0.5, "STATOR LAMINATION 1:2", label_xy=(320, 100))
    e.circle((0, 0), sod / 2, fc=FILLS["steel"], lw=0.8)
    e.circle((0, 0), sb / 2, fc="white", lw=0.8)
    ns = 24
    for k in range(ns):
        a = 2 * math.pi * (k + 0.5) / ns
        r0, r1, w = sb / 2 + 1.5, sod / 2 - 18, 7.0
        ca, sa = math.cos(a), math.sin(a)
        pts = [(r0, -w / 3), (r1, -w / 2), (r1, w / 2), (r0, w / 3)]
        e.poly([(x * ca - y * sa, x * sa + y * ca) for x, y in pts], fc=FILLS["copper"], lw=0.3, z=4)
    e.center_mark((0, 0), sod / 2 + 6)
    e.dia((0, 0), sod / 2, 40)
    e.dia((0, 0), sb / 2, 200, out=40)
    e.text((0, -sod / 2 - 12), "24 slots, 3-phase, 2-pole, 1 mm slot opening", 5)
    sh.notes([f"Rated ~{DP['power']['shaft_kW']:.0f} kW at {DP['inputs']['speed_rpm']:,} rpm "
              f"({DP['power']['shaft_torque_Nm']:.0f} N.m); 500 Hz electrical at 30k rpm (2-pole).",
              "Air gap 1 mm to CFRP sleeve (rotor Ø70 over sleeve, stator bore Ø72).",
              "Housing: revolve the section, cut helical groove with Swept Cut (Helix/Spiral, pitch 20).",
              "Stator stack is press-fit into the groove sleeve; end windings modelled as simple rings.",
              "Motor cavity is vented to suction - for CFD this region is NOT in the main gas path."],
             x=14, y=82, size=5.6)
    sh.save(pdf, OUT / "TC-130.png")


def sheet_bearings(pdf):
    sh = Sheet("TC-140", "MAGNETIC & TOUCHDOWN BEARINGS", "0.7:1 / 1:1 / 2:1", 11, TOTAL,
               material="Stators: laminated Si-steel (radial), solid Co-Fe / low-C steel (axial); Cu coils")
    x0, x1, bore, od = L.RADIAL_BRG_FRONT
    f = sh.view(85, 180, 0.7, "RADIAL BEARING STATOR 0.7:1", label_xy=(85, 108))
    f.circle((0, 0), od / 2, fc=FILLS["steel"], lw=0.8)
    f.circle((0, 0), 52, fc="white", lw=0.5)
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 8
        ca, sa = math.cos(a), math.sin(a)
        w = 13.0
        pole = [(bore / 2, -w / 2), (54, -w / 2), (54, w / 2), (bore / 2, w / 2)]
        f.poly([(x * ca - y * sa, x * sa + y * ca) for x, y in pole], fc=FILLS["steel"], lw=0.5, z=4)
        coil = [(34, -w / 2 - 6), (52, -w / 2 - 6), (52, w / 2 + 6), (34, w / 2 + 6)]
        f.poly([(x * ca - y * sa, x * sa + y * ca) for x, y in coil], fc=FILLS["copper"], lw=0.4, z=3)
    f.circle((0, 0), 25, fc=FILLS["steel"], lw=0.6, z=5)
    f.text((0, 0), "ROTOR\nØ50", 5)
    f.center_mark((0, 0), od / 2 + 5)
    f.dia((0, 0), od / 2, 30, text=f"Ø{od:.0f}")
    f.dia((0, 0), bore / 2, 300, out=70, text=f"Ø{bore:.0f} POLE BORE (0.5 mm gap)")
    f.text((0, -od / 2 - 10), f"8 poles (4 N-S pairs, X/Y axes), stack {x1 - x0:.0f} mm, pole width 13", 5)
    # axial bearing section
    a = sh.view(185 - 550, 180, 1.0, "AXIAL BEARING SECTION 1:1", label_xy=(215, 96))
    (ax0, ax1, ab, aod), (bx0, bx1, _, _) = L.AXIAL_BRG
    t0, t1, tod = L.THRUST_DISK
    for (x0_, x1_) in ((ax0, ax1), (bx0, bx1)):
        a.mirror_rect(x0_, ab / 2, x1_, aod / 2, fc=FILLS["steel"])
        for r0, r1 in ((30, 40), (48, 58)):
            a.mirror_rect(x0_ + 3 if x0_ > t1 else x0_, r0, x1_ if x0_ > t1 else x1_ - 3, r1, fc=FILLS["copper"], lw=0.4)
    a.mirror_rect(t0, 20, t1, tod / 2, fc=FILLS["rotor"])
    a.mirror_rect(550, 0, 600, 20, fc=FILLS["rotor"])
    a.centerline((545, 0), (605, 0))
    a.dim((ax0, aod / 2), (bx1, aod / 2), 5, fmt="{:.0f}")
    a.dim((t0, tod / 2), (t1, tod / 2), 12, fmt="{:.0f}")
    a.dim((ax1, -30), (t0, -30), 0.1, text=f"{t0 - ax1:.1f} gap")
    a.dim((t1, -30), (bx0, -30), 0.1, text=f"{bx0 - t1:.1f} gap")
    a.dim((bx1 + 5, 0), (bx1 + 5, tod / 2), 0.1, orient="v", text=f"Ø{tod:.0f} DISK")
    a.dim((bx1 + 14, 0), (bx1 + 14, aod / 2), 0.1, orient="v", text=f"Ø{aod:.0f}")
    # touchdown bearing
    t = sh.view(325 - 2 * 207, 180, 2.0, "TOUCHDOWN BEARING 2:1", label_xy=(345, 112))
    tx0, tx1, tb, tod2 = L.TOUCHDOWN_FRONT
    t.mirror_rect(tx0, tb / 2, tx1, tod2 / 2, fc="white")
    for sgn in (1, -1):
        t.circle(((tx0 + tx1) / 2, sgn * (tb / 2 + tod2 / 2) / 2), (tod2 - tb) / 4 - 1, fc="#999", lw=0.4)
    t.mirror_rect(tx0 - 3, 0, tx1 + 3, 15, fc=FILLS["rotor"], lw=0.4)
    t.centerline((tx0 - 6, 0), (tx1 + 6, 0))
    t.dim((tx0, tod2 / 2), (tx1, tod2 / 2), 5, fmt="{:.0f}")
    t.dim((tx1 + 6, -tod2 / 2), (tx1 + 6, tod2 / 2), 4, orient="v", text=f"Ø{tod2:.0f}")
    t.dim((tx0 - 6, -tb / 2), (tx0 - 6, tb / 2), -4, orient="v", text=f"Ø{tb:.1f}")
    sh.notes(["Bearings are electromagnets - for CAD model laminations/coils as simple solids.",
              "Radial: 0.5 mm air gap; touchdown (ceramic hybrid angular-contact pair): 0.2 mm radial",
              "  clearance, so the rotor lands on touchdowns before touching magnetic poles.",
              "Axial: two stators straddle the thrust disk, 0.5 mm nominal gap each side.",
              "Position sensors (eddy-current) sit next to each radial bearing and at the shaft end."],
             x=14, y=62, size=5.6)
    sh.save(pdf, OUT / "TC-140.png")


def sheet_cfd(pdf):
    sh = Sheet("CFD-001", "CFD FLUID DOMAINS & BOUNDARY CONDITIONS", "1.6:1", 12, TOTAL)
    v = sh.view(70 - 1.6 * 75, 95, 1.6, "DOMAIN A: STAGE-1 SINGLE PASSAGE (TurboGrid -> CFX)  1.6:1", label_xy=(130, 82))
    hub, shr = FP["hub1"], FP["shr1"]
    ext_in = 20.0
    inlet = np.array([[L.IMP1_X0 - ext_in, hub[0, 1]], [L.IMP1_X0 - ext_in, shr[0, 1]]])
    poly = np.vstack([[L.IMP1_X0 - ext_in, shr[0, 1]], shr, [[L.D1_SHR_X, L.R2], [L.D1_SHR_X, L.R3],
                      [L.D1_HUB_X, L.R3], [L.D1_HUB_X, L.R2]], hub[::-1], [[L.IMP1_X0 - ext_in, hub[0, 1]]]])
    v.poly(poly, fc=FILLS["fluid"], lw=0.8)
    v.poly(blade_region(1), fc=FILLS["blade"], lw=0.4, alpha=0.8)
    v.line(inlet, lw=2.5, c="#2a7f2a")
    v.line([[L.D1_SHR_X, L.R3], [L.D1_HUB_X, L.R3]], lw=2.5, c="#b03030")
    v.line([[L.D1_SHR_X - 0.5, L.R2], [L.D1_HUB_X + 0.5, L.R2]], lw=0.6, c="#7030a0", ls="--")
    v.centerline((L.IMP1_X0 - ext_in - 3, 0), (L.D1_HUB_X + 10, 0))
    v.leader(tuple(inlet.mean(0)), (L.IMP1_X0 - ext_in + 5, 3), "INLET: P0, T0, axial")
    v.leader((L.D1_SHR_X + 3, L.R3), (L.D1_HUB_X + 10, L.R3 + 10), "OUTLET: mass flow (or avg static P)")
    v.leader((L.D1_HUB_X, L.R2 + 2), (L.D1_HUB_X + 10, L.R2 + 12), "R-S interface (Stage/Mixing-plane)\nif diffuser in stationary domain")
    v.leader((shr[20, 0], shr[20, 1]), (L.IMP1_X0 - 15, L.R3 - 5), "SHROUD: counter-rotating wall\n(stationary in abs. frame)")
    v.leader((hub[25, 0], hub[25, 1]), (L.IMP1_X0 + 40, 10), "HUB: rotating wall")
    v.dim((L.IMP1_X0 - ext_in, 5), (L.IMP1_X0, 5), -4, fmt="{:.0f}")
    rows = [("Item", "Setting"),
            ("Mass flow (full wheel)", f"{DP['cycle']['mdot_kg_s']:.3f} kg/s"),
            ("Per passage (7 main+splitter)", f"{DP['cycle']['mdot_kg_s'] / 7:.4f} kg/s"),
            ("Inlet P0 / T0", f"{DP['cycle']['P_suction_kPa']:.1f} kPa / {DP['cycle']['T_suction_C'] + 273.15:.2f} K"),
            ("Rotation", f"{DP['inputs']['speed_rpm']:,} rpm about +X"),
            ("Periodicity", "360/7 = 51.43 deg rotational"),
            ("Tip clearance", f"{L.TIP_CLEARANCE} mm at shroud"),
            ("Turbulence", "SST k-ω, y+ ~1 on blades"),
            ("Fluid", "R-513A real gas (RGP / Peng-Robinson)"),
            ("Expected stage-1 PR", f"~{S1['PR']:.2f} (meanline)")]
    sh.table(270, 270, rows, [52, 70], title="DOMAIN A SETUP", size=5.4, row_h=4.2)
    sh.notes(["DOMAIN B (full-stage / 360 deg, Fluent or CFX): extract the fluid volume of the assembly",
              "  (SpaceClaim Volume Extract) from suction flange to discharge flange, rotor stationary",
              "  domains split at impeller inlet/outlet; Frozen Rotor interfaces; ~10-20 M cells.",
              "Run DOMAIN A first (minutes-hours on a workstation); B only once A is converged and sane.",
              "Do NOT mesh the motor, bearings, or electronics for the aero CFD.",
              "Speed lines: vary back-pressure/mass flow at 24k, 27k, 30k, 33k rpm to map surge/choke.",
              "Post: PR_tt, η_tt (from h0 or T0/P0 with real gas), blade loading, Mach number at 50% span."],
             x=14, y=62, size=5.6)
    sh.save(pdf, OUT / "CFD-001.png")


def export_flowpath_curves():
    d = L.ROOT / "cad_curves"
    def w(name, pts):
        (d / name).write_text("\n".join(f"{x:.4f} {r:.4f} 0.0000" for x, r in pts) + "\n")
    f = FP
    shroud = np.vstack([f["inlet_shr"], f["shr1"], [[L.D1_SHR_X, L.R2], [L.D1_SHR_X, L.R3]],
                        f["bend_out"], f["rc_shr"], f["shr2"], [[L.D2_SHR_X, L.R2], [L.D2_SHR_X, L.R3]]])
    hub = np.vstack([f["nose"], f["hub1"], [[L.D1_HUB_X, L.R2], [L.D1_HUB_X, L.R3]], f["bend_in"],
                     f["rc_hub"], f["hub2"], [[L.D2_HUB_X, L.R2], [L.D2_HUB_X, L.R3]]])
    w("flowpath_shroud.txt", shroud)
    w("flowpath_hub.txt", hub)
    rows = ["theta_deg,section_dia_mm,centre_radius_mm,area_mm2,x_mm"]
    rows += [f"{t:.1f},{dd:.3f},{rc:.3f},{math.pi * dd * dd / 4:.1f},{L.VOLUTE_X:.3f}" for t, dd, rc in VOL]
    (d / "volute_sections.csv").write_text("\n".join(rows) + "\n")
    rows = ["segment,x_from_mm,x_to_mm,diameter_mm,function"]
    rows += [f"{i},{a:.2f},{b:.2f},{dd:.1f},{n}" for i, (a, b, dd, n) in enumerate(L.SHAFT, 1)]
    (d / "rotor_segments.csv").write_text("\n".join(rows) + "\n")


def main():
    export_flowpath_curves()
    with PdfPages(OUT / "Turbocor_drawing_set.pdf") as pdf:
        sheet_cover(pdf)
        sheet_ga_section(pdf)
        sheet_ga_exterior(pdf)
        sheet_impeller(pdf, 1)
        sheet_impeller(pdf, 2)
        sheet_shaft(pdf)
        sheet_igv(pdf)
        sheet_casing(pdf)
        sheet_volute(pdf)
        sheet_motor(pdf)
        sheet_bearings(pdf)
        sheet_cfd(pdf)
    print("wrote", OUT / "Turbocor_drawing_set.pdf")


if __name__ == "__main__":
    main()
