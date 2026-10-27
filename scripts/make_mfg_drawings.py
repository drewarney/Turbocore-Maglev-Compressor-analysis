"""
Manufacturing drawing set for the impellers: drawings/Manufacturing_drawing_set.pdf
(+ PNG per sheet).

    python scripts/impeller_geometry.py && python scripts/cam_analysis.py && python scripts/make_mfg_drawings.py

MFG-101 / MFG-102  impeller machining drawings (datums, GD&T, inspection plan)
MFG-110            blank, turning operations and 5-axis workholding
MFG-120            5-axis CAM plan: operations, tools, tool access, flank-milling check
"""
import json
import math

import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Arc, Circle, Polygon, Rectangle

import impeller_geometry as IG
import layout as LY
from drafting import CL, DIM, FILLS, INK, Sheet

ROOT = IG.ROOT
OUT = ROOT / "drawings"
CAM = json.loads((ROOT / "docs" / "cam_summary.json").read_text())
TOTAL = 4
RB = LY.SHAFT_D_IMP / 2
BP = LY.BACKPLATE_T
GLYPH = {"flatness": "⏥", "perpendicularity": "⊥", "runout": "↗", "parallelism": "∥"}


# ------------------------------------------------------------------ GD&T helpers (paper mm)
def fcf(ax, x, y, sym, tol, datums=(), target=None, h=5.0):
    """Feature control frame with its lower-left corner at (x, y); optional leader to target."""
    cells = [6.0, max(9.0, 1.6 * len(tol) + 3)] + [5.0] * len(datums)
    cx = x
    for w in cells:
        ax.add_patch(Rectangle((cx, y), w, h, fill=True, fc="white", ec=INK, lw=0.5, zorder=9))
        cx += w
    sx, sy = x + 3.0, y + h / 2
    if sym in GLYPH:
        ax.text(sx, sy, GLYPH[sym], fontsize=7, ha="center", va="center", zorder=10)
    elif sym == "profile":                 # profile of a surface: closed semicircle
        ax.add_patch(Arc((sx, sy - 1.0), 3.6, 3.6, theta1=0, theta2=180, lw=0.6, ec=INK, zorder=10))
        ax.plot([sx - 1.8, sx + 1.8], [sy - 1.0, sy - 1.0], lw=0.6, c=INK, zorder=10)
    elif sym == "position":
        ax.add_patch(Circle((sx, sy), 1.3, fill=False, lw=0.6, ec=INK, zorder=10))
        ax.plot([sx - 2, sx + 2], [sy, sy], lw=0.5, c=INK, zorder=10)
        ax.plot([sx, sx], [sy - 2, sy + 2], lw=0.5, c=INK, zorder=10)
    ax.text(x + cells[0] + cells[1] / 2, sy, tol, fontsize=5.6, ha="center", va="center", zorder=10)
    cx = x + cells[0] + cells[1]
    for d in datums:
        ax.text(cx + 2.5, sy, d, fontsize=5.8, ha="center", va="center", zorder=10)
        cx += 5.0
    if target is not None:
        ax.annotate("", xy=target, xytext=(x, y + h / 2), zorder=8,
                    arrowprops=dict(arrowstyle="-|>", lw=0.45, color=INK, shrinkA=0, shrinkB=0,
                                    mutation_scale=5))
    return cx


def datum(ax, letter, foot, box, foot_dir="down"):
    """Datum feature symbol: filled triangle on the feature at `foot`, letter box at `box`."""
    fx, fy = foot
    s = 1.6
    tri = {"down": [(fx - s, fy), (fx + s, fy), (fx, fy + 1.8 * s)],
           "left": [(fx, fy - s), (fx, fy + s), (fx - 1.8 * s, fy)],
           "right": [(fx, fy - s), (fx, fy + s), (fx + 1.8 * s, fy)],
           "up": [(fx - s, fy), (fx + s, fy), (fx, fy - 1.8 * s)]}[foot_dir]
    ax.add_patch(Polygon(tri, closed=True, fc=INK, ec=INK, lw=0.3, zorder=9))
    tx = sum(p[0] for p in tri) / 3
    ty = sum(p[1] for p in tri) / 3
    ax.plot([tx, box[0]], [ty, box[1]], lw=0.45, c=INK, zorder=8)
    ax.add_patch(Rectangle((box[0] - 2.5, box[1] - 2.5), 5, 5, fc="white", ec=INK, lw=0.6, zorder=9))
    ax.text(box[0], box[1], letter, fontsize=6.5, ha="center", va="center", weight="bold", zorder=10)


def paper(v, p):
    return tuple(v.P([p])[0])


def part_outline(g):
    hub, L = g["hub"], g["L"]
    body = np.vstack([[[0, RB]], hub, [[L + BP, hub[-1, 1]], [L + BP, RB]]])
    blade = np.vstack([hub, g["shroud"][::-1]])
    return body, blade


# ------------------------------------------------------------------ MFG-101 / 102
def sheet_part(pdf, stage):
    g = IG.stage_blades(stage)
    c = CAM[f"stage{stage}"]
    hub, shroud, L = g["hub"], g["shroud"], g["L"]
    r2, r1h, r1t = hub[-1, 1], hub[0, 1], shroud[0, 1]
    sh = Sheet(f"MFG-10{stage}", f"IMPELLER STAGE {stage} - MACHINING", "2.5:1 / 0.9:1", stage, TOTAL,
               material="7075-T651 bar (UT inspected) or 2618-T61 forging")
    ax = sh.ax
    v = sh.view(40, 128, 2.5, "SECTION X-X (MERIDIONAL)  2.5:1", label_xy=(100, 116))
    body, blade = part_outline(g)
    v.poly(blade, fc=FILLS["blade"], lw=0.6)
    v.poly(body, fc=FILLS["alu"], hatch="////", lw=0.8)
    v.line(shroud, lw=1.0)
    v.centerline((-6, 0), (L + BP + 8, 0))
    v.line([(0, RB), (L + BP, RB)], lw=0.8)
    # dimensions
    v.dim((L + BP, 0), (L + BP, r2), 22, orient="v", text=f"Ø{2 * r2:.2f} ±0.02")
    v.dim((L + BP, 0), (L + BP, RB), 10, orient="v", text=f"Ø{2 * RB:.0f} H7 (+0.018/0)")
    v.dim((0, 0), (0, r1h), -7, orient="v", text=f"Ø{2 * r1h:.2f}")
    v.dim((0, 0), (0, r1t), -16, orient="v", text=f"Ø{2 * r1t:.2f}")
    v.dim((0, r2 + 1), (L + BP, r2 + 1), 10, text=f"{L + BP:.2f} ±0.05")
    v.dim((shroud[-1, 0], r2), (L, r2), 4, text=f"b2 {L - shroud[-1, 0]:.2f}")
    v.dim((L, r2), (L + BP, r2), 4, text=f"{BP:.1f}")
    v.leader(tuple(hub[22] + [0.4, -0.6]), (L + 15, r1h + 9), f"R{CAM['inputs']['fillet_recommended_mm']:.1f} ±0.3 HUB FILLET\n"
             f"(TC-10{stage} shows R1.0, see note 4)")
    # datums on the paper
    pA = paper(v, (L + BP, (RB + r2) / 2 + 6))
    datum(ax, "A", pA, (pA[0] + 10, pA[1]), foot_dir="right")
    pB = paper(v, (L + BP - 6, RB))
    datum(ax, "B", pB, (pB[0] - 4, pB[1] - 9), foot_dir="up")
    # feature control frames
    xa = paper(v, (L + BP, 0))[0]
    fcf(ax, 168, 250, "flatness", "0.005", target=paper(v, (L + BP, r2 - 8)))
    fcf(ax, 168, 242, "runout", "0.010", ("A", "B"), target=paper(v, (L + BP - 1.5, r2)))
    fcf(ax, 168, 150, "perpendicularity", "Ø0.005", ("A",), target=paper(v, (L - 6, RB)))
    k = len(shroud) // 3
    fcf(ax, 30, 272, "profile", "0.05", ("A", "B"), target=paper(v, tuple(shroud[k])))
    ax.text(62, 274.5, "BLADE-TIP (SHROUD) LINE: sets the 0.30 mm running clearance", fontsize=5.0, va="center")
    fcf(ax, 168, 170, "profile", "0.10", ("A", "B"), target=paper(v, tuple(hub[31])))
    ax.text(197, 172.5, "HUB FLOW SURFACE", fontsize=5.0, va="center")
    fcf(ax, 14, 112, "runout", "0.020", ("A", "B"), target=paper(v, (0, (r1h + RB) / 2)))
    ax.text(43, 114.5, "EYE FACE", fontsize=5.0, va="center")
    fcf(ax, 168, 222, "profile", "0.08", ("A", "B", "C"))
    ax.text(204, 224.5, "ALL BLADE SURFACES, MAIN + SPLITTER (14x)", fontsize=5.0, va="center")
    fcf(ax, 168, 214, "position", "0.10", ("A", "B", "C"))
    ax.text(204, 216.5, "BLADE ANGULAR SPACING 7x 51.43°, SPLITTERS +25.71°", fontsize=5.0, va="center")

    # view from inlet
    fv = sh.view(338, 200, 0.9, "VIEW FROM INLET  0.9:1  (BLADE 1 = DATUM C)", label_xy=(338, 147))
    d = ROOT / "cad_curves" / f"stage{stage}"
    mh, ms = np.loadtxt(d / "main_hub_camber.txt"), np.loadtxt(d / "main_shroud_camber.txt")
    sp_h = np.loadtxt(d / "splitter_hub_camber.txt")
    fv.circle((0, 0), r2, fc=FILLS["alu"], lw=0.9)
    fv.circle((0, 0), r1t, ls="--", lw=0.5)
    fv.circle((0, 0), r1h, fc="#f4f4f4", lw=0.6)
    fv.circle((0, 0), RB, fc="white", lw=0.6)
    pitch = 2 * math.pi / 7
    for n in range(7):
        cs, sn = math.cos(n * pitch), math.sin(n * pitch)
        rot = lambda p: np.column_stack([-(p[:, 0] * cs - p[:, 1] * sn), p[:, 0] * sn + p[:, 1] * cs])
        fv.line(rot(mh), lw=1.2 if n else 2.0, c=INK if n else "#b03030")
        fv.line(rot(ms), lw=0.5, c="#666")
        fv.line(rot(sp_h), lw=0.9, c="#8a5a00")
        tip = rot(mh[-1:])[0]
        fv.text(tuple(tip * 1.13), str(n + 1), 6, weight="bold")
    fv.center_mark((0, 0), r2 + 6)
    tipc = (-mh[-1, 0], mh[-1, 1])
    pc = paper(fv, (tipc[0] * 0.8, tipc[1] * 0.8))
    datum(ax, "C", pc, (pc[0] + 18, pc[1] + 4), foot_dir="up")
    fv.text((0, -r2 - 9), "ROTATION CW VIEWED FROM INLET.  Red = blade 1 (datum C), brown = splitters", 5.2)

    # inspection plan
    rows = [("#", "Characteristic", "Requirement", "Method"),
            ("1", "Bore B", "Ø18 H7, Ra 0.4", "Air gauge / bore mic"),
            ("2", "Back face A", "Flat 0.005, Ra 0.4", "CMM / surface plate"),
            ("3", "Tip OD", f"Ø{2 * r2:.2f} ±0.02, runout 0.010", "CMM, on mandrel"),
            ("4", "Blade tip line", "Profile 0.05 |A|B|", "CMM scan"),
            ("5", "Blade surfaces", "Profile 0.08 |A|B|C|", "Blue-light scan vs CAD"),
            ("6", "Blade thickness", f"{IG.T_HUB:.1f} / {IG.T_SHROUD:.1f} ±0.05 hub/tip", "Scan section cuts"),
            ("7", "Hub fillets", "R1.5 ±0.3", "Radius gauge / scan"),
            ("8", "Flow-surface finish", "Ra ≤ 0.8 µm", "Profilometer, 3 blades"),
            ("9", "Balance", f"G{CAM['inputs']['balance_grade']:.1f}: U ≤ {c['balance_U_gmm']:.3f} g·mm", "2-plane balancer"),
            ("10", "Overspeed", "34,500 rpm (115 %), growth ≤ 0.01", "Spin pit, re-measure 1, 3")]
    sh.table(150, 140, rows, [7, 33, 46, 40], title="INSPECTION PLAN", size=5.0, row_h=3.9)
    key = [("Item", "Value"),
           ("Finished mass", f"{c['mass_kg'] * 1000:.0f} g"),
           ("Blades", "7 main + 7 splitter, 40° backswept"),
           ("Tip / exit width", f"Ø{2 * r2:.2f} / b2 {g['s']['b2'] * 1000:.2f}"),
           ("Max blade height", f"{c['height_le']:.1f} mm at LE"),
           ("Tightest passage", f"{c['crit_gap_hub']:.2f} mm at m = {c['crit_m']:.2f}"),
           ("Design speed", "30,000 rpm, U2 162 m/s"),
           ("CAM plan", "MFG-110, MFG-120"),
           ("Blade data", f"cad_curves/stage{stage}/")]
    sh.table(282, 140, key, [30, 50], title="KEY DATA", size=5.0, row_h=3.9)
    sh.notes([
        "All dimensions after machining, at 20 °C. General tolerances ISO 2768-mK.",
        "Datums: A = back face, B = bore (A and B finished in one lathe setup, OP30), C = blade 1.",
        "Flow surfaces (hub, blades) Ra ≤ 0.8 µm, no visible step between toolpaths > 0.01 mm.",
        "Hub fillets R1.5 replace the R1.0 on TC-10x so the Ø3 finishing ball cuts them (docs/05).",
        "Leading edges elliptical 2:1, hand-blended after OP40. TE as machined. Other edges 0.2 max.",
        "Balance ISO 21940-11 G1.0 in two planes (eye nose, back rim); remove metal only at rim.",
        "Spin test at 115 % speed before final balance; re-check items 1 and 3.",
        "Mark S/N and a blade-1 dot on the back face, r < 25 mm, low-stress dot peen.",
        "Study drawing for a reverse-engineered model - not for production without stress review.",
    ], x=14, y=100, size=5.4)
    sh.save(pdf, OUT / f"MFG-10{stage}.png")


# ------------------------------------------------------------------ MFG-110
def sheet_blank(pdf):
    g = IG.stage_blades(2)
    hub, shroud, L = g["hub"], g["shroud"], g["L"]
    r2 = hub[-1, 1]
    bar_r, bar_l, z0 = 55.0, 52.0, -6.0
    sh = Sheet("MFG-110", "IMPELLER BLANK, TURNING & 5-AXIS FIXTURE", "2:1 / 1:1", 3, TOTAL,
               material="Bar Ø110 x 52, 7075-T651 (both stages)")
    ax = sh.ax
    v = sh.view(40, 138, 2.0, "BLANK SECTION, STAGE 2 SHOWN  2:1", label_xy=(95, 126))
    v.rect(z0, 0, z0 + bar_l, bar_r, fc="#f6f6f6", ec="#888", lw=0.5)
    env = np.vstack([[[0, RB], [0, shroud[0, 1]]], shroud, [[L + BP, r2], [L + BP, RB]]])
    v.poly(env, fc=FILLS["blade"], lw=0.7)
    body, _ = part_outline(g)
    v.poly(body, fc=FILLS["alu"], hatch="////", lw=0.8)
    v.centerline((z0 - 4, 0), (z0 + bar_l + 6, 0))
    v.dim((z0, 0), (z0, bar_r), -8, orient="v", text="Ø110 BAR")
    v.dim((z0, bar_r), (z0 + bar_l, bar_r), 6, text=f"{bar_l:.0f} SAW CUT")
    v.dim((L + BP, 0), (L + BP, r2), 22, orient="v", text=f"Ø{2 * r2:.2f}")
    v.leader((0.5 * (z0 + 0), bar_r - 6), (z0 + bar_l + 8, bar_r + 2), "grey: removed by turning (OP20/OP30)")
    v.leader(tuple(0.5 * (hub[25] + shroud[25])), (L + 10, 35), "yellow: removed by 5-axis (OP40)\n"
             f"{CAM['stage2']['v_remove_cm3']:.0f} cm³ stage 2, {CAM['stage1']['v_remove_cm3']:.0f} cm³ stage 1")
    v.leader((L / 2, RB + 4), (L + 10, 16), "hatched: finished hub body")

    rows = [("OP", "Machine", "Work", "Datum / holding"),
            ("10", "Saw", "Cut Ø110 bar to 52, UT-inspected stock", "-"),
            ("20", "CNC lathe", "Face eye side, turn blade-tip (shroud) envelope +0.1,", "3-jaw on bar OD"),
            ("", "", "tip OD +0.2, drill + rough bore Ø17", ""),
            ("30", "CNC lathe", "Face back face A, finish bore B Ø18 H7,", "Soft jaws on tip OD"),
            ("", "", "finish tip OD + tip envelope (one setup with A, B)", ""),
            ("40", "5-axis mill", "Blades + hub from solid, see MFG-120", "Mandrel on A + B"),
            ("50", "Bench", "Deburr, blend LEs 2:1, clean", "-"),
            ("60", "CMM / scan", "Inspection plan items 1-8", "A, B, C"),
            ("70", "Balancer", "2-plane balance G1.0", "Balancing arbor on B"),
            ("80", "Spin pit", "115 % overspeed, re-inspect, final balance", "Arbor on B")]
    sh.table(214, 272, rows, [9, 20, 68, 34], title="ROUTING", size=5.0, row_h=3.9)

    # fixture section, 1:1
    f = sh.view(300, 106, 1.0, "5-AXIS FIXTURE (SECTION)  1:1", label_xy=(300, 78))
    f.rect(-55, -20, 55, 0, fc=FILLS["steel"], lw=0.7)                       # zero-point pallet
    f.rect(-20, 0, 20, 60, fc=FILLS["steel"], lw=0.7, hatch="\\\\\\\\")       # riser
    f.rect(-RB + 0.01, 60, RB - 0.01, 70, fc=FILLS["steel"], lw=0.7)          # pilot Ø18 g5
    hub2 = np.column_stack([hub[:, 1], 60 + (L + BP - hub[:, 0])])
    part = np.vstack([[[RB, 60], [r2, 60]], hub2[::-1], [[RB, 60 + L + BP]]])
    f.poly(part, fc=FILLS["alu"], lw=0.8)
    f.poly(part * [-1, 1], fc=FILLS["alu"], lw=0.8)
    tipline = np.column_stack([shroud[:, 1], 60 + (L + BP - shroud[:, 0])])
    f.line(tipline, lw=0.5, ls="--", c="#777")
    f.line(tipline * [-1, 1], lw=0.5, ls="--", c="#777")
    f.rect(-11, 60 + L + BP, 11, 60 + L + BP + 4, fc=FILLS["rotor"], lw=0.7)  # washer Ø22
    f.rect(-4, 64, 4, 60 + L + BP + 9, fc="#bbbbbb", lw=0.6)                   # M8 screw
    f.centerline((0, -24), (0, 60 + L + BP + 14))
    f.leader((40, -10), (58, -6), "zero-point pallet")
    f.leader((20, 30), (58, 20), "riser Ø40 x 60: clears\nholder at 90° tilt")
    f.leader((RB, 66), (58, 46), "pilot Ø18 g5 in bore B,\nshoulder seats face A")
    f.leader((11, 60 + L + BP + 2), (58, 100), "Ø22 washer + M8 screw\n(< hub eye Ø25.9)")
    f.leader((r2 - 3, 63), (58, 72), "impeller, face A down;\ndashed = blade tips")
    sh.notes([
        "OP30 finishes A, B, tip OD and the tip envelope in one chucking; tip runout and the 0.30 mm clearance depend on it.",
        "Tip contour is turned, not milled, so the 5-axis paths never touch the blade-tip line.",
        "OP40 creates datum C (blade 1). No dowel needed: probe tip OD + face A, start at 0°.",
        "Riser height and washer size set by tool-holder clearance; check in CAM simulation.",
        "Same blank and fixture for both stages; stage 1 removes more (longer, taller blades).",
    ], x=14, y=100, size=5.4)
    sh.save(pdf, OUT / "MFG-110.png")


# ------------------------------------------------------------------ MFG-120
def sheet_cam(pdf):
    sh = Sheet("MFG-120", "5-AXIS CAM PLAN (OP40)", "NTS", 4, TOTAL)
    c1, c2 = CAM["stage1"], CAM["stage2"]
    T = CAM["tools"]
    ops = [("Step", "Tool", "Strategy", "Stock", "S2 min", "S1 min")]
    plan = [("OP40-1 rough T1", "T1", "5-axis adaptive / multiblade rough", "0.30"),
            ("OP40-2 rest-rough T2", "T2", "Rest rough at splitter LE, corners", "0.30"),
            ("OP40-3 semi-finish T3", "T3", "Blade + hub semi, 0.49 stepover", "0.10"),
            ("OP40-4 finish hub T3", "T3", "Hub floor, flowline, 0.22 stepover", "0"),
            ("OP40-5 finish blades T3 (point)", "T3", "Blades point-milled, 0.22 stepover", "0"),
            ("OP40-6 fillet pencil T4 (only if R1.0 kept)", "T4", "Only if R1.0 fillets are kept", "0"),
            ("OP40-7 deburr T5", "T5", "Edge break, not LEs", "-")]
    for key, tool, strat, stock in plan:
        ops.append((key.split()[0], tool, strat, stock, f"{c2['minutes'][key]:.0f}", f"{c1['minutes'][key]:.0f}"))
    tot = lambda c: sum(v for k, v in c["minutes"].items() if "T4" not in k)
    ops.append(("TOTAL", "", "R1.5 fillets, point-finished blades", "", f"{tot(c2):.0f}", f"{tot(c1):.0f}"))
    ops.append(("ALT", "T3", "Stage 2: flank (swarf) finish blades", "",
                f"{tot(c2) - c2['minutes']['OP40-5 finish blades T3 (point)'] + c2['flank_finish_minutes']:.0f}", "n/a"))
    sh.table(14, 280, ops, [17, 9, 56, 10, 12, 12], title="OPERATIONS (estimated minutes incl. 1.35x motion factor)",
             size=5.0, row_h=3.9)
    tools = [("T", "Tool", "F mm/min")] + [(k, t["desc"], f"{t['feed']:.0f}") for k, t in T.items()]
    sh.table(14, 220, tools, [7, 72, 16], title=f"TOOLS (carbide, {CAM['inputs']['spindle_rpm']:,} rpm)",
             size=5.0, row_h=3.9)
    comp = [("Check", "Stage 1", "Stage 2"),
            ("Tightest gap (hub)", f"{c1['crit_gap_hub']:.2f} mm", f"{c2['crit_gap_hub']:.2f} mm"),
            ("Blade height there", f"{c1['crit_height']:.1f} mm", f"{c2['crit_height']:.1f} mm"),
            ("Reach / Ø for T3", f"{c1['reach_over_d_T3']:.1f}", f"{c2['reach_over_d_T3']:.1f}"),
            ("Max ruling twist", f"{c1['twist_max']:.1f}°", f"{c2['twist_max']:.1f}°"),
            ("Flank error, R1.5", f"{c1['flank_error_mm']['R1.5']:.3f} mm", f"{c2['flank_error_mm']['R1.5']:.3f} mm"),
            ("Flank finish OK (≤0.05)?", "no: point-mill", "yes"),
            ("Metal removed (OP40)", f"{c1['v_remove_cm3']:.0f} cm³", f"{c2['v_remove_cm3']:.0f} cm³")]
    sh.table(14, 182, comp, [34, 26, 26], title="TOOL ACCESS & FLANK-MILLING CHECK", size=5.0, row_h=3.9)

    # charts
    fig = sh.fig
    def axes(x, y, w, h):
        a = fig.add_axes([x / 420, y / 297, w / 420, h / 297])
        a.tick_params(labelsize=5, length=2)
        a.grid(lw=0.3, alpha=0.5)
        return a
    a1 = axes(140, 200, 120, 70)
    for c, ls, lab in ((c1, "--", "stage 1"), (c2, "-", "stage 2")):
        p = c["profile"]
        a1.plot(p["m"], p["gap_hub"], ls, c="#1f4e9e", lw=0.9, label=f"gap at hub, {lab}")
        a1.plot(p["m"], p["height"], ls, c="#b03030", lw=0.9, label=f"blade height, {lab}")
    need_t1 = T["T1"]["d"] + 2 * CAM["inputs"]["rough_stock_mm"] + 2 * 0.5
    a1.axhline(need_t1, c="#555", lw=0.6, ls=":")
    a1.text(0.02, need_t1 + 0.3, f"T1 needs {need_t1:.1f} mm", fontsize=4.8, color="#555")
    a1.axhline(T["T3"]["d"], c="#8a5a00", lw=0.6, ls=":")
    a1.text(0.62, T["T3"]["d"] + 0.3, "T3 Ø3", fontsize=4.8, color="#8a5a00")
    a1.axvline(IG.SPLITTER_START, c="#888", lw=0.5)
    a1.text(IG.SPLITTER_START + 0.01, 19.5, "splitter LE", fontsize=4.8, color="#666")
    a1.set_xlabel("meridional position m (0 = LE, 1 = TE)", fontsize=5.5)
    a1.set_ylabel("mm", fontsize=5.5)
    a1.set_title("Passage width vs blade height", fontsize=6.5)
    a1.legend(fontsize=4.5, loc="upper right", ncol=2, frameon=False)

    a2 = axes(285, 200, 115, 70)
    for c, ls, lab in ((c1, "--", "stage 1"), (c2, "-", "stage 2")):
        p = c["profile"]
        tw = np.radians(p["twist"])
        a2.plot(p["m"], 1.5 * (1 - np.cos(tw / 2)) * 1000, ls, c="#b03030", lw=0.9, label=f"R1.5, {lab}")
        a2.plot(p["m"], 1.0 * (1 - np.cos(tw / 2)) * 1000, ls, c="#1f4e9e", lw=0.9, label=f"R1.0, {lab}")
    a2.axhline(50, c="#555", lw=0.6, ls=":")
    a2.text(0.02, 52, "blade profile tolerance 0.05 mm", fontsize=4.8, color="#555")
    a2.set_xlabel("meridional position m", fontsize=5.5)
    a2.set_ylabel("µm", fontsize=5.5)
    a2.set_title("Flank-milling deviation from ruling twist", fontsize=6.5)
    a2.legend(fontsize=4.5, loc="upper right", ncol=2, frameon=False)

    # critical section: unwrapped blade-to-blade view at the hub, stage 2
    g = IG.stage_blades(2)
    zh, th, bh, mh = g["main_h"]
    msl = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(zh, axis=0).T))])
    a3 = axes(150, 66, 120, 108)
    pitch = 2 * math.pi / 7
    k = int(np.argmin(np.abs(mh - c2["crit_m"])))
    rk = zh[k, 1]
    half = 0.5 * IG.T_HUB / np.cos(np.radians(bh))        # half thickness, measured along r·θ
    for off, col, start in ((0, "#444", 0.0), (pitch / 2, "#8a5a00", IG.SPLITTER_START), (pitch, "#444", 0.0)):
        sel = mh >= start
        y = rk * (th[sel] + off)
        a3.fill_between(msl[sel], y - half[sel], y + half[sel], color=col, lw=0)
    cy = rk * (th[k] + pitch / 4)
    a3.add_patch(Circle((msl[k], cy), T["T3"]["d"] / 2, fill=False, ec="#1f4e9e", lw=1.0))
    a3.add_patch(Circle((msl[k], cy), T["T1"]["d"] / 2 + CAM["inputs"]["rough_stock_mm"] + 0.5,
                        fill=False, ec="#b03030", lw=0.8, ls="--"))
    a3.text(msl[k] - 13, rk * (th[k] + pitch) - 1.5,
            f"normal gap {c2['crit_gap_hub']:.2f} mm (blade 2.0 mm thick at hub)\n"
            "blue: T3 Ø3 fits with ~0.9 mm each side\n"
            "red dashed: T1 Ø5 + 0.3 stock + 0.5 clearance does not", fontsize=4.8, va="top")
    a3.set_aspect("equal")
    a3.set_xlim(msl[k] - 14, msl[k] + 14)
    a3.set_ylim(rk * (th[k] - 0.15), rk * (th[k] + pitch + 0.15))
    a3.set_xlabel("meridional distance along hub, mm", fontsize=5.5)
    a3.set_ylabel("r·θ at the hub, mm", fontsize=5.5)
    a3.set_title(f"Stage 2 hub section at the splitter LE (m = {c2['crit_m']:.2f})", fontsize=6.5)

    sh.notes([
        "Blade CAM: hyperMILL Impeller, Mastercam Blade Expert, NX Turbomachinery, SolidCAM Multiblade.",
        "Fusion 360 (Manufacturing Ext.): no blade wizard; use swarf + multi-axis contour + rest roughing.",
        "Export STEP from SolidWorks; select hub, blade-tip, blade, splitter and fillet faces in the wizard.",
        "Tilt strategy: lead 3-5°, lean from blade, interpolate tool axis between hub and shroud.",
        "Rough with constant stock; finish hub before blades so the blade root sees the final floor.",
        "Finish blades top-down in 2-3 depth steps so uncut metal below supports the thin tip.",
        "Simulate full machine + holder; check the Ø3 neck against the next blade at m ≈ 0.3.",
        "Times are first-order estimates (scripts/cam_analysis.py); trust the CAM simulation.",
    ], x=285, y=180, size=5.0)
    sh.save(pdf, OUT / "MFG-120.png")


def main():
    with PdfPages(OUT / "Manufacturing_drawing_set.pdf") as pdf:
        sheet_part(pdf, 1)
        sheet_part(pdf, 2)
        sheet_blank(pdf)
        sheet_cam(pdf)
    print("wrote", OUT / "Manufacturing_drawing_set.pdf")


if __name__ == "__main__":
    main()
