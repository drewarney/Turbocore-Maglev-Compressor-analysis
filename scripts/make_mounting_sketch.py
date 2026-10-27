"""
Schematic: two ways to mount the impellers on the rotor (half-sections, to scale from
layout.py). drawings/SK-001_impeller_mounting.png / .pdf

    python scripts/make_mounting_sketch.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

import impeller_geometry as IG
import layout as L
from drafting import FILLS, INK

OUT = L.ROOT / "drawings"
RB = L.SHAFT_D_IMP / 2
X1, X2, BP = L.IMP1_X0, L.IMP2_X0, L.BACKPLATE_T
SP0, SP1 = X1 + L.IMP_L + BP, X2                 # spacer sleeve
SH = X2 + L.IMP_L + BP                           # shaft shoulder (seal sleeve)
NUT0, NUT1 = L.NOSE_X0, X1


def impeller(ax, stage, x0, bore_r=RB, hatch="////"):
    hub, shroud, Lz = IG.meridional(IG.DP[f"stage{stage}"])
    body = np.vstack([[[x0, bore_r]], hub + [x0, 0], [[x0 + Lz + BP, hub[-1, 1]], [x0 + Lz + BP, bore_r]]])
    blade = np.vstack([hub + [x0, 0], (shroud + [x0, 0])[::-1]])
    ax.add_patch(Polygon(blade, fc=FILLS["blade"], ec=INK, lw=0.6))
    ax.add_patch(Polygon(body, fc=FILLS["alu"], ec=INK, lw=0.9, hatch=hatch))
    ax.text(x0 + 0.55 * Lz, hub[-1, 1] - 14, f"stage-{stage}\nimpeller", ha="center", fontsize=7)


def rect(ax, x0, y0, x1, y1, fc, hatch=None, lw=0.8):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=fc, ec=INK, lw=lw, hatch=hatch))


def arrow(ax, a, b, c="#b03030", lw=1.4, style="-|>"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, mutation_scale=9, lw=lw, color=c, zorder=9))


def base(ax, title):
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(70, 262)
    ax.set_ylim(-8, 68)
    ax.plot([72, 240], [0, 0], c="#b03030", lw=0.6, ls=(0, (8, 2, 1.5, 2)))
    ax.text(70, 62, title, fontsize=10, weight="bold")
    # shaft: stub up to the shoulder, then the seal sleeve / bearing journal
    rect(ax, NUT0 + 2, 0, SH, RB, FILLS["steel"])
    rect(ax, SH, 0, 232, 16, FILLS["steel"])
    ax.text(222, 7, "shaft\n(steel)", ha="center", fontsize=7)


fig, (a1, a2) = plt.subplots(2, 1, figsize=(11.5, 9.2))

# ------------------------------------------------------------- (a) clamped stack
base(a1, "(a) Clamped stack: nut / tie bolt, torque by face friction")
impeller(a1, 1, X1)
impeller(a1, 2, X2)
rect(a1, SP0, RB, SP1, 12, FILLS["rotor"])
a1.text(0.5 * (SP0 + SP1), 13.5, "spacer", ha="center", fontsize=7)
rect(a1, NUT0, RB - 4, NUT1, 11, FILLS["rotor"])
a1.text(NUT0 - 1, 13, "nose nut\n(threaded\non stub)", ha="right", fontsize=7)
a1.plot([NUT0 + 2, NUT1], [RB - 4, RB - 4], c=INK, lw=0.4)
for xx in np.arange(NUT0 + 3, NUT1, 1.2):                      # thread
    a1.plot([xx, xx + 0.6], [RB - 4, RB - 3.2], c=INK, lw=0.4)
# clamp load path (compression through the stack) and bolt tension
y = 10.5
for xa, xb in ((NUT1 - 3, X1 + 4), (SP0 - 4, SP0 + 4), (SP1 - 4, SP1 + 4), (SH - 4, SH + 3)):
    arrow(a1, (xa, y), (xb, y))
arrow(a1, (SH - 2, 3.5), (NUT0 + 6, 3.5), c="#1f4e9e")
a1.text(0.5 * (NUT0 + SH), 1.2, "stub in TENSION (preload F ≈ 30 kN)", color="#1f4e9e", ha="center", fontsize=7)
a1.text(SP0 + 2, 19, "stack in COMPRESSION", color="#b03030", fontsize=7)
for xf in (X1, SP0, SP1, X2 + L.IMP_L + BP):                   # friction faces carrying torque
    a1.plot([xf, xf], [RB + 0.5, 12], c="#2a8a2a", lw=2.6, alpha=0.8)
a1.text(SH + 3, 45, "green faces carry the torque by friction:\n"
        "T = μ·F·r_m  →  F ≈ 16 kN for 36 N·m\n(μ 0.15, r_m 15 mm), ×2 margin\n\n"
        "bore: pilot fit (H7/g5 or light\ninterference) only centres the wheel",
        fontsize=7, va="top")
a1.text(SH + 3, 63, "+ easy to assemble and service\n+ balance stays repeatable\n− needs flat, square faces (datum A)",
        fontsize=7, va="top", color="#333")

# ------------------------------------------------------------- (b) shrink fit
base(a2, "(b) Shrink (interference) fit: torque by bore pressure")
impeller(a2, 1, X1)
impeller(a2, 2, X2)
rect(a2, SP0, RB, SP1, 12, FILLS["rotor"])
rect(a2, NUT0 + 4, RB - 3, NUT1, 10, FILLS["rotor"])
a2.text(NUT0 + 3, 12, "light lock nut\n(axial retention only)", ha="right", fontsize=7)
for x0 in (X1, X2):                                             # interference band, exaggerated
    a2.add_patch(Rectangle((x0, RB - 0.9), L.IMP_L + BP, 0.9, fc="#d04040", ec="none", alpha=0.6))
    for xx in np.linspace(x0 + 3, x0 + L.IMP_L, 6):
        arrow(a2, (xx, RB + 4.5), (xx, RB + 0.2), c="#b03030", lw=1.0)
a2.text(X1 + 2, RB - 4.6, "interference δ (exaggerated)", color="#b03030", fontsize=7)
a2.text(SH + 3, 47, "assemble: heat impeller (~150 °C) or\nfreeze shaft, slide on, let it cool\n\n"
        "contact pressure p on the bore carries\ntorque AND centres the wheel\n\n"
        "at 30,000 rpm the Al bore grows ≈ 0.016 mm\n+ 0.009 mm more Al-vs-steel expansion at 60 °C\n"
        "→ need δ > ≈ 0.03 mm on Ø18 so it stays tight",
        fontsize=7, va="top")
a2.text(SH + 3, 64, "+ no torque on the faces, very stiff\n− hard to remove; heating can change\n   7075-T6 temper above ~120 °C\n− fit loosens with speed and temperature",
        fontsize=7, va="top", color="#333")

fig.text(0.5, 0.015, "Half-sections above the rotor axis, to scale (layout.py). Blades in yellow, hub body hatched. "
         "Study schematic - the real Turbocor mounting is not published.", ha="center", fontsize=7, color="#555")
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(OUT / "SK-001_impeller_mounting.png", dpi=150)
fig.savefig(OUT / "SK-001_impeller_mounting.pdf")
print("wrote", OUT / "SK-001_impeller_mounting.png")
