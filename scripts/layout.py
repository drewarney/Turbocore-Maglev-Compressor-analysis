"""
Single source of truth for the compressor layout (all mm).

Coordinate system used everywhere (CAD, drawings, CFD):
  X = machine / rotor axis, X = 0 at the suction flange face, +X toward the motor/rear.
  r = radius from the rotor axis.  In SolidWorks sketch on the Top/Front plane with
  the horizontal construction line through the origin as the revolve axis.
  Machine base (bottom of feet) is at Z = -AXIS_HEIGHT.

Impeller curve files (cad_curves/stageN) use a LOCAL frame: Z = axis, Z = 0 at the
impeller eye.  Place them in the assembly at X = IMP1_X0 / IMP2_X0.
"""
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DP = json.loads((ROOT / "docs" / "design_point.json").read_text())
S1, S2 = DP["stage1"], DP["stage2"]

# ---------------------------------------------------------------- envelope
LENGTH, WIDTH, HEIGHT = 790.0, 480.0, 465.0     # Turbocor TT-class envelope (approx.)
AXIS_HEIGHT = 200.0                             # rotor axis above bottom of feet
HOUSING_OD = 300.0                              # motor / bearing housing
HOUSING_WALL = 12.0

# ---------------------------------------------------------------- flanges
SUCTION_ID, SUCTION_FLANGE_OD, SUCTION_FLANGE_T = 102.0, 210.0, 20.0     # DN100 / 4 in
DISCHARGE_ID, DISCHARGE_FLANGE_OD, DISCHARGE_FLANGE_T = 52.5, 150.0, 18.0  # DN50 / 2 in

# ---------------------------------------------------------------- aero path
TIP_CLEARANCE = 0.30          # impeller shroud running clearance
IGV_X = 40.0                  # IGV pivot plane (vane spans X 30-70)
IGV_COUNT, IGV_CHORD, IGV_T = 8, 40.0, 0.12   # NACA 0012, chord mm
IMP1_X0 = 95.0                # stage-1 eye plane
IMP_L = 0.30 * S1["D2"] * 1000
R2 = S1["D2"] * 500
B2_1, B2_2 = S1["b2"] * 1000, S2["b2"] * 1000
R3 = 1.55 * R2                # vaneless diffuser exit radius
BACKPLATE_T = 3.0
CROSSOVER_GAP = 8.0           # diaphragm thickness between diffuser 1 and return channel
RC_INNER_R = 40.0             # return channel turns axial below this radius
DESWIRL_COUNT = 12
IMP2_X0 = None                # computed below
SHAFT_D_IMP = 18.0            # impeller bore / shaft stub

# stage 1 exit / diffuser 1 walls
X1_TIP_HUB = IMP1_X0 + IMP_L
X1_TIP_SHR = X1_TIP_HUB - B2_1
B3_1 = 0.9 * B2_1
D1_SHR_X = X1_TIP_SHR + 0.5 * (B2_1 - B3_1)
D1_HUB_X = D1_SHR_X + B3_1
# crossover U-bend and return channel (same width as diffuser exit)
RC_SHR_X = D1_HUB_X + CROSSOVER_GAP       # upstream wall -> becomes stage-2 HUB
RC_HUB_X = RC_SHR_X + B3_1                # downstream wall -> becomes stage-2 SHROUD
BEND_CX = 0.5 * (D1_HUB_X + RC_SHR_X)
BEND_R_IN = 0.5 * CROSSOVER_GAP
BEND_R_OUT = BEND_R_IN + B3_1
IMP2_X0 = RC_HUB_X + 11.0
X2_TIP_HUB = IMP2_X0 + IMP_L
X2_TIP_SHR = X2_TIP_HUB - B2_2
B3_2 = 0.9 * B2_2
D2_SHR_X = X2_TIP_SHR + 0.5 * (B2_2 - B3_2)
D2_HUB_X = D2_SHR_X + B3_2
VOLUTE_X = 0.5 * (D2_SHR_X + D2_HUB_X)

# ---------------------------------------------------------------- rotor (x0, x1, diameter)
NOSE_X0 = IMP1_X0 - 10.0
SHAFT = [
    (NOSE_X0, IMP1_X0, 22.0, "impeller nut / nose cone"),
    (IMP1_X0, X1_TIP_HUB + BACKPLATE_T, SHAFT_D_IMP, "stage-1 impeller seat"),
    (X1_TIP_HUB + BACKPLATE_T, IMP2_X0, 24.0, "interstage spacer sleeve"),
    (IMP2_X0, X2_TIP_HUB + BACKPLATE_T, SHAFT_D_IMP, "stage-2 impeller seat"),
    (X2_TIP_HUB + BACKPLATE_T, 205.0, 32.0, "seal sleeve"),
    (205.0, 225.0, 30.0, "front touchdown bearing journal"),
    (225.0, 285.0, 50.0, "front radial bearing rotor laminations"),
    (285.0, 300.0, 40.0, "shaft"),
    (300.0, 470.0, 70.0, "PM motor rotor (magnets + carbon-fibre sleeve)"),
    (470.0, 490.0, 40.0, "shaft"),
    (490.0, 550.0, 50.0, "rear radial bearing rotor laminations"),
    (550.0, 600.0, 40.0, "thrust-disk seat"),
    (600.0, 622.0, 30.0, "rear touchdown bearing journal"),
    (622.0, 632.0, 20.0, "axial / speed sensor target"),
]
THRUST_DISK = (570.0, 580.0, 120.0)       # x0, x1, OD
ROTOR_X0, ROTOR_X1 = NOSE_X0, 632.0

# ---------------------------------------------------------------- stationary internals
RADIAL_BRG_FRONT = (230.0, 280.0, 51.0, 150.0)   # x0, x1, bore, OD (0.5 mm radial air gap)
RADIAL_BRG_REAR = (495.0, 545.0, 51.0, 150.0)
AXIAL_BRG = [(553.0, 567.0, 44.0, 150.0), (583.0, 597.0, 44.0, 150.0)]  # two stators
TOUCHDOWN_FRONT = (207.0, 223.0, 30.4, 55.0)     # ball bearing, 0.2 mm radial clearance
TOUCHDOWN_REAR = (603.0, 619.0, 30.4, 55.0)
STATOR = (305.0, 465.0, 72.0, 230.0)             # lamination stack x0, x1, bore, OD
END_WINDING = 28.0
COOLING_GROOVE_PITCH, COOLING_GROOVE_DEPTH, COOLING_GROOVE_W = 20.0, 4.0, 8.0
HOUSING_X0, HOUSING_X1 = D2_HUB_X + 4.0, 650.0   # motor/bearing housing
REAR_COVER = (650.0, 668.0)
ELECTRONICS = (200.0, 700.0, 160.0, HEIGHT - AXIS_HEIGHT)  # x0, x1, z0, z1 (rel. axis)
MAINS_BOX = (668.0, LENGTH, -60.0, 160.0)               # rear mains-input box
FEET = [(130.0, 190.0), (540.0, 600.0)]                 # x ranges, base plate 12 thick
FOOT_SPAN = 380.0


# ---------------------------------------------------------------- helpers
def bezier(p, n=41):
    t = np.linspace(0, 1, n)[:, None]
    p = np.asarray(p, float)
    return ((1 - t) ** 3) * p[0] + 3 * (1 - t) ** 2 * t * p[1] + 3 * (1 - t) * t ** 2 * p[2] + t ** 3 * p[3]


def arc(cx, cy, r, a0, a1, n=30):
    a = np.radians(np.linspace(a0, a1, n))
    return np.column_stack([cx + r * np.cos(a), cy + r * np.sin(a)])


def load_meridional(stage, x0):
    """Hub and shroud lines as (x, r) arrays in machine coordinates."""
    d = ROOT / "cad_curves" / f"stage{stage}"
    hub = np.loadtxt(d / "hub_meridional.txt")
    shr = np.loadtxt(d / "shroud_meridional.txt")
    return (np.column_stack([hub[:, 2] + x0, hub[:, 0]]),
            np.column_stack([shr[:, 2] + x0, shr[:, 0]]))


def flowpath():
    """Continuous hub-side and shroud-side walls from suction flange to volute inlet.

    Returns dict of named (x, r) polylines. 'hub' lines are the inner (small-x/low-r)
    boundaries seen by the gas; 'shroud' lines the casing side.
    """
    h1, s1 = load_meridional(1, IMP1_X0)
    h2, s2 = load_meridional(2, IMP2_X0)
    r_in = SUCTION_ID / 2
    nose_r = h1[0, 1]
    # inlet: straight duct, IGV plane, contraction to the stage-1 eye
    x_c = IGV_X + 0.75 * IGV_CHORD                                # contraction starts at IGV TE
    inlet_shr = np.vstack([[0, r_in],
                           bezier([(x_c, r_in), (x_c + 12, r_in),
                                   (IMP1_X0 - 8, s1[0, 1] + TIP_CLEARANCE),
                                   (IMP1_X0, s1[0, 1] + TIP_CLEARANCE)], 15)])
    nose = arc(IMP1_X0, 0, nose_r, 180, 90, 12)
    nose[:, 0] = IMP1_X0 + (nose[:, 0] - IMP1_X0) * 10 / nose_r   # 10 mm long ellipse
    shr1 = s1 + [0, 0]
    shr1[:, 0] -= TIP_CLEARANCE                                    # casing offset
    # diffuser 1, crossover, return channel
    diff1_shr = np.array([[D1_SHR_X, R2], [D1_SHR_X, R3]])
    diff1_hub = np.array([[D1_HUB_X, R2], [D1_HUB_X, R3]])
    bend_out = arc(BEND_CX, R3, BEND_R_OUT, 180, 0)
    bend_in = arc(BEND_CX, R3, BEND_R_IN, 180, 0)
    # return channel: upstream wall becomes stage-2 hub, downstream wall becomes stage-2 shroud
    rc_hub = np.vstack([[RC_SHR_X, R3],
                        bezier([(RC_SHR_X, RC_INNER_R), (RC_SHR_X, h2[0, 1] + 2),
                                (IMP2_X0 - 8, h2[0, 1]), (IMP2_X0, h2[0, 1])], 15)])
    rc_shr = np.vstack([[RC_HUB_X, R3],
                        bezier([(RC_HUB_X, RC_INNER_R + 6), (RC_HUB_X, s2[0, 1] + 4),
                                (IMP2_X0 - 4, s2[0, 1] + TIP_CLEARANCE),
                                (IMP2_X0, s2[0, 1] + TIP_CLEARANCE)], 15)])
    shr2 = s2.copy()
    shr2[:, 0] -= TIP_CLEARANCE
    diff2_shr = np.array([[D2_SHR_X, R2], [D2_SHR_X, R3]])
    diff2_hub = np.array([[D2_HUB_X, R2], [D2_HUB_X, R3]])
    return dict(inlet_shr=inlet_shr, nose=nose, hub1=h1, shr1=shr1, diff1_shr=diff1_shr,
                diff1_hub=diff1_hub, bend_out=bend_out, bend_in=bend_in, rc_hub=rc_hub,
                rc_shr=rc_shr, hub2=h2, shr2=shr2, diff2_shr=diff2_shr, diff2_hub=diff2_hub,
                imp_shr1=s1, imp_shr2=s2)


def volute_sections(n=9):
    """Circular external volute, constant angular momentum. Returns list of (theta_deg, d, rc)."""
    from CoolProp import CoolProp as CP
    AS = CP.AbstractState("HEOS", "R1234yf&R134a")
    AS.set_mass_fractions([0.56, 0.44])
    AS.update(CP.PT_INPUTS, S2["P_out"], S2["T_out"])
    q = DP["cycle"]["mdot_kg_s"] / AS.rhomass()           # m3/s at volute
    K = S2["Ct2"] * (R2 / 1000)                            # angular momentum Ct*r
    out = []
    for th in np.linspace(0, 360, n):
        d = 0.0
        for _ in range(50):                                # A = Q th rc / (2 pi K)
            rc = R3 + d / 2 + 2.0                          # 2 mm tongue/lip offset
            area = q * math.radians(th) * (rc / 1000) / (2 * math.pi * K)
            d = 2000 * math.sqrt(area / math.pi)
        out.append((th, d, R3 + d / 2 + 2.0))
    return out, q


def deswirl_angles():
    """Return-channel vane inlet/outlet metal angles (deg from radial)."""
    r_in = R3 / 1000
    ct = S1["Ct2"] * (R2 / R3)                             # free vortex in diffuser 1
    rho = S1["rho2"] * 1.08                                # slight diffusion
    cm = DP["cycle"]["mdot_kg_s"] / (rho * 2 * math.pi * r_in * B3_1 / 1000)
    return math.degrees(math.atan2(ct, cm)), 0.0


if __name__ == "__main__":
    print(f"IMP1_X0 {IMP1_X0}  IMP2_X0 {IMP2_X0:.1f}  L {IMP_L:.1f}  R2 {R2:.2f}  R3 {R3:.1f}")
    print(f"diff1 x {D1_SHR_X:.2f}-{D1_HUB_X:.2f}  RC x {RC_SHR_X:.2f}-{RC_HUB_X:.2f}  "
          f"diff2 x {D2_SHR_X:.2f}-{D2_HUB_X:.2f}")
    v, q = volute_sections()
    print("volute q", q, [(round(t), round(d, 1), round(rc, 1)) for t, d, rc in v])
    print("deswirl", deswirl_angles())
