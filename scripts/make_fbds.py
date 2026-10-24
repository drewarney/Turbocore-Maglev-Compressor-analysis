"""Free-body and control-volume diagrams for the compressor design -> calcs/FBD_set.pdf + PNGs."""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyArrowPatch, Rectangle, FancyBboxPatch, Circle, Wedge, Polygon, Arc

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "calcs" / "hand_calcs.json").read_text())
OUT = ROOT / "calcs"
INK, BLUE, RED, GRN, PUR, GRY, ORG = "#1a1a1a", "#1f5fbf", "#c0392b", "#1e8449", "#6c3fb5", "#7f8c8d", "#d35400"

def page(title, number):
    fig = plt.figure(figsize=(11, 8.5))
    ax = fig.add_axes([0.04, 0.04, 0.92, 0.88]); ax.set_xlim(0, 110); ax.set_ylim(0, 85); ax.axis("off")
    fig.text(0.04, 0.95, f"FBD-{number}", fontsize=11, color=GRY, weight="bold")
    fig.text(0.11, 0.95, title, fontsize=15, weight="bold", color=INK)
    fig.text(0.04, 0.015, "Turbocor-class compressor study: free-body / control-volume diagrams. Numbers from scripts/hand_calcs.py.",
             fontsize=7.5, color=GRY)
    return fig, ax

def arrow(ax, x0, y0, x1, y1, c=INK, lw=2.0, ms=14, style="-|>"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=ms, lw=lw, color=c, shrinkA=0, shrinkB=0))

def box(ax, x, y, w, h, text, fc="#eef2f5", ec=INK, fs=11, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4", fc=fc, ec=ec, lw=1.4, ls=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)

def eqs(ax, x, y, lines, fs=10.5, title="Equations"):
    ax.text(x, y, title, fontsize=11, weight="bold")
    for i, ln in enumerate(lines):
        ax.text(x, y - 3.4 * (i + 1), ln, fontsize=fs, family="DejaVu Sans")

figs = []

# ---------- FBD-1 cycle
c = D["cycle"]
fig, ax = page("Chiller refrigeration cycle: system control volumes", 1)
box(ax, 8, 55, 26, 10, "EVAPORATOR\n(chilled water side)")
box(ax, 70, 55, 26, 10, "COMPRESSOR\n(2-stage centrifugal)", fc="#fdf2e9")
box(ax, 70, 20, 26, 10, "CONDENSER\n(air-cooled)")
box(ax, 8, 20, 26, 10, "EXPANSION VALVE\n(EXV)")
arrow(ax, 34.6, 60, 69.4, 60, BLUE); ax.text(52, 62, f"(1) suction vapour  {c['P_ev_kPa']:.0f} kPa, {c['T1_C']:.1f} °C", ha="center", fontsize=9.5)
arrow(ax, 83, 54.4, 83, 30.6, RED); ax.text(84.5, 42, f"(2) discharge\n{c['P_cd_kPa']:.0f} kPa", fontsize=9.5)
arrow(ax, 69.4, 25, 34.6, 25, BLUE); ax.text(52, 27, f"(3) subcooled liquid, {c['Tc_C']-5:.1f} °C", ha="center", fontsize=9.5)
arrow(ax, 21, 30.6, 21, 54.4, BLUE); ax.text(22.5, 42, "(4) 2-phase\nmixture", fontsize=9.5)
arrow(ax, 21, 76, 21, 66, GRN, ms=18); ax.text(23, 72, f"Q̇_evap = {c['Q_evap_kW']:.0f} kW ({c['tons']:.0f} tons) IN", fontsize=10, color=GRN)
arrow(ax, 83, 76, 83, 66, PUR, ms=18); ax.text(85, 72, "Ẇ_shaft IN", fontsize=10, color=PUR)
arrow(ax, 83, 19, 83, 9, RED, ms=18); ax.text(85, 12, "Q̇_cond OUT", fontsize=10, color=RED)
ax.add_patch(Rectangle((66, 50), 34, 20, fill=False, ls="--", lw=1.4, ec=PUR)); ax.text(66.5, 70.8, "CV: compressor", color=PUR, fontsize=9)
eqs(ax, 36, 46, [f"Energy, evaporator CV:   Q̇_evap = ṁ (h₁ − h₄)",
                 f"h₄ = h₃ (throttling) = {c['h4']:.1f} kJ/kg,   h₁ = {c['h1']:.1f} kJ/kg",
                 f"ṁ = {c['Q_evap_kW']:.1f} / ({c['h1']:.1f} − {c['h4']:.1f}) = {c['mdot']:.3f} kg/s",
                 f"Pressure ratio = P₂/P₁ = {c['PR']:.2f}  →  per stage √PR = {c['PR_stage']:.3f}"], fs=9.5)
figs.append(("FBD-1_cycle", fig))

# ---------- FBD-2 compressor CV
p = D["power"]
fig, ax = page("Compressor control volume: first law (steady flow)", 2)
ax.add_patch(Polygon([(35, 30), (35, 60), (75, 66), (75, 24)], closed=True, fc="#fdf2e9", ec=INK, lw=1.6))
ax.text(55, 45, "COMPRESSOR\n(stages 1 + 2)", ha="center", va="center", fontsize=12)
ax.add_patch(Rectangle((30, 18), 50, 54, fill=False, ls="--", lw=1.6, ec=PUR)); ax.text(30.5, 73, "control surface", color=PUR, fontsize=9)
arrow(ax, 6, 45, 34.5, 45, BLUE, ms=18); ax.text(6, 48.5, f"ṁ = {c['mdot']:.3f} kg/s\nh₀₁ = {c['h1']:.1f} kJ/kg\nP₀₁ = {c['P_ev_kPa']:.0f} kPa", fontsize=9.5)
arrow(ax, 75.5, 45, 104, 45, RED, ms=18); ax.text(82, 48.5, f"h₀₂ = h₀₁ + Δh₀\nP₀₂ = {c['P_cd_kPa']:.0f} kPa", fontsize=9.5)
arrow(ax, 55, 8, 55, 23.5, PUR, ms=18); ax.text(57, 12, f"Ẇ_gas = {p['P_gas']:.1f} kW (shaft work on gas)", color=PUR, fontsize=10)
ax.text(55, 76, "Q̇ ≈ 0 (adiabatic; motor-cooling flow handled separately)", ha="center", fontsize=9.5, color=GRY)
eqs(ax, 4, 30, [r"Steady-flow energy:  Ẇ = ṁ (h₀₂ − h₀₁)    (Q̇ ≈ 0, ΔPE ≈ 0)",
                f"Ideal (isentropic):  Δh₀s = h₂s − h₁ = {c['dhs_total']:.2f} kJ/kg",
                f"Actual (meanline):  Δh₀ = {p['dh_total']:.2f} kJ/kg  → η_s = {p['eta_overall']:.3f}",
                f"Ẇ_gas = {c['mdot']:.3f} × {p['dh_total']:.2f} = {p['P_gas']:.1f} kW"], fs=9.5)
figs.append(("FBD-2_compressor_CV", fig))

# ---------- FBD-3 impeller angular momentum CV (front view)
s = D["stage1"]
fig, ax = page("Impeller control volume: angular momentum (Euler turbomachine equation)", 3)
cx, cy, R2, R1 = 32, 42, 26, 11
ax.add_patch(Circle((cx, cy), R2, fc="#eef2f5", ec=INK, lw=1.5))
ax.add_patch(Circle((cx, cy), R1, fc="white", ec=INK, lw=1.2))
for k in range(7):
    a = math.radians(90 + k * 360 / 7)
    pts = [(cx + (R1 + (R2 - R1) * u) * math.cos(a - 0.9 * u), cy + (R1 + (R2 - R1) * u) * math.sin(a - 0.9 * u)) for u in [i / 20 for i in range(21)]]
    ax.plot(*zip(*pts), color=ORG, lw=2)
ax.add_patch(Circle((cx, cy), R2 + 2.5, fill=False, ls="--", ec=PUR, lw=1.5)); ax.text(cx + 17, cy + 27, "control surface", color=PUR, fontsize=9)
ax.add_patch(Arc((cx, cy), 10, 10, theta1=200, theta2=340, color=PUR, lw=2)); arrow(ax, cx + 4.6, cy - 2.3, cx + 4.9, cy - 0.5, PUR)
ax.text(cx - 3, cy - 8.5, "T_shaft", color=PUR, fontsize=11, weight="bold")
ax.text(cx, cy, "ω", ha="center", va="center", fontsize=16)
# exit momentum flux arrow at top
ax.plot([cx], [cy + R2], "o", color=RED)
arrow(ax, cx, cy + R2, cx - 9, cy + R2, RED); ax.text(cx - 17, cy + R2 + 2, "Cθ₂ (swirl out)", color=RED, fontsize=10)
arrow(ax, cx, cy + R2, cx, cy + R2 + 7, RED); ax.text(cx + 1, cy + R2 + 6, "Cr₂", color=RED, fontsize=10)
ax.text(cx + R1 * 0.2, cy - R1 - 3, "inlet: Cθ₁ = 0 (IGVs open)", fontsize=9.5, color=BLUE, ha="center")
eqs(ax, 64, 72, ["Angular momentum about the shaft axis:",
                 "  T_shaft = ṁ (r₂Cθ₂ − r₁Cθ₁)",
                 "Power:  Ẇ = T ω = ṁ (U₂Cθ₂ − U₁Cθ₁)",
                 "With Cθ₁ = 0:  Δh₀ = U₂ Cθ₂",
                 "Slip (Wiesner):  σ = 1 − √(cos β₂b) / Z^0.7",
                 f"  Z = {s['Z']}, β₂b = {s['beta2b']:.0f}° → σ = {s['sigma']:.3f}",
                 "Cθ₂ = σU₂ − Cm₂ tan β₂b,   Cm₂ = φ₂U₂",
                 f"ψ = Δh₀/U₂² = σ − φ₂ tan β₂b = {s['psi']:.3f}",
                 f"U₂ = {s['U2']:.1f} m/s → Δh₀ = {s['dh0']:.2f} kJ/kg",
                 f"D₂ = 60U₂/(πN) = {s['D2_mm']:.1f} mm  (N = {s['N']:,} rpm)",
                 f"Stage-1 torque = ṁΔh₀/ω = {D['cycle']['mdot']*s['dh0']*1e3/s['omega']:.1f} N·m"], fs=10)
figs.append(("FBD-3_euler_CV", fig))

# ---------- FBD-4 velocity triangles
fig, ax = page("Velocity triangles (kinematics): stage-1 inlet tip and exit, to scale", 4)
k = 0.18
def vec(x0, y0, dx, dy, col, lab, off=(0, 0)):
    arrow(ax, x0, y0, x0 + dx * k, y0 + dy * k, col, lw=2.4)
    ax.text(x0 + dx * k / 2 + off[0], y0 + dy * k / 2 + off[1], lab, color=col, fontsize=11, weight="bold", ha="center")
ox, oy = 16, 30
vec(ox, oy, 0, s["Cm1"], BLUE, f"C₁ = Cm₁\n= {s['Cm1']:.1f}", (-6, 0))
vec(ox, oy, s["U1t"], 0, GRY, f"U₁t = {s['U1t']:.1f}", (0, -3))
arrow(ax, ox + s["U1t"] * k, oy, ox, oy + s["Cm1"] * k, ORG, lw=2.4)
ax.text(ox + s["U1t"] * k / 2 + 4, oy + s["Cm1"] * k / 2 + 1, f"W₁t = {s['W1t']:.1f}", color=ORG, fontsize=11, weight="bold")
ax.text(ox, 58, "INLET (blade tip)", fontsize=12, weight="bold")
ax.text(ox, 55, f"β₁t = atan(U₁t/Cm₁) = {s['beta1t']:.1f}° from axial;  M₁rel = W₁t/a₁ = {s['M1rel']:.2f}", fontsize=9.5)
ox = 52
vec(ox, oy, s["U2"], 0, GRY, f"U₂ = {s['U2']:.1f}", (0, -3))
vec(ox, oy, s["Ct2"], s["Cm2"], BLUE, f"C₂ = {s['C2']:.1f}", (-6, 2))
arrow(ax, ox + s["U2"] * k, oy, ox + s["Ct2"] * k, oy + s["Cm2"] * k, ORG, lw=2.4)
ax.text(ox + (s["U2"] + s["Ct2"]) * k / 2 + 3, oy + s["Cm2"] * k / 2 + 1, f"W₂ = {math.hypot(s['U2']-s['Ct2'], s['Cm2']):.1f}", color=ORG, fontsize=11, weight="bold")
# blade direction (no slip) dashed
bx = ox + s["U2"] * k; Wt_blade = s["Cm2"] * math.tan(math.radians(s["beta2b"]))
ax.plot([bx, bx - Wt_blade * k], [oy, oy + s["Cm2"] * k], ls="--", color=GRY)
ax.text(bx - Wt_blade * k - 1, oy + s["Cm2"] * k + 1.5, "blade direction (β₂b = 40°)", fontsize=8.5, color=GRY, ha="center")
ax.text(ox, 58, "EXIT (r₂ = 51.7 mm)", fontsize=12, weight="bold")
ax.text(ox, 55, f"Cθ₂ = σU₂ − Cm₂tanβ₂b = {s['Ct2']:.1f};  α₂ = atan(Cθ₂/Cm₂) = {s['alpha2']:.1f}° from radial", fontsize=9.5)
ax.plot([8, 8 + 50 * k], [12, 12], color=INK, lw=2); ax.text(8 + 50 * k + 1, 11.4, "50 m/s", fontsize=9)
eqs(ax, 30, 16, ["Vector relation at every point:  C = U + W   (absolute = blade + relative)",
                 "Slip: the gas leaves at a smaller swirl than the blade angle implies (σ < 1)"], fs=10, title="")
figs.append(("FBD-4_velocity_triangles", fig))

# ---------- FBD-5 fluid particle in rotating passage
fig, ax = page("Fluid particle in the rotating passage (relative frame): forces per unit volume", 5)
ax.add_patch(Wedge((20, 10), 70, 58, 82, width=55, fc="#f4f7f9", ec=GRY))
ax.text(20, 8, "axis (ω)", fontsize=9, color=GRY, ha="center")
px, py = 32, 50
ax.add_patch(Rectangle((px - 4, py - 3), 8, 6, angle=0, fc="#d6eaf8", ec=INK, lw=1.5))
ax.text(px, py, "dV", ha="center", va="center")
arrow(ax, px - 12, py, px - 4.2, py, BLUE); ax.text(px - 18, py + 1.5, "p dA", color=BLUE, fontsize=11)
arrow(ax, px + 12, py, px + 4.2, py, BLUE); ax.text(px + 12.5, py + 1.5, "(p + ∂p/∂r dr) dA", color=BLUE, fontsize=11)
arrow(ax, px, py + 3.2, px + 3, py + 13, RED); ax.text(px + 3.5, py + 12, "centrifugal  ρω²r dV  (outward)", color=RED, fontsize=10.5)
arrow(ax, px, py - 3.2, px - 9, py - 11, PUR); ax.text(px - 30, py - 13, "Coriolis  −2ρ ω × W dV", color=PUR, fontsize=10.5)
arrow(ax, px - 2, py - 3.2, px + 8, py - 10, GRN); ax.text(px + 9, py - 11, "blade force (normal to blade)", color=GRN, fontsize=10.5)
arrow(ax, px + 4.2, py + 1, px + 4.2 + 6, py + 4, ORG); ax.text(px + 10.5, py + 4.5, "W (relative velocity)", color=ORG, fontsize=10)
eqs(ax, 62, 72, ["Momentum, rotating frame (steady):",
                 "  ρ(W·∇)W = −∇p + ρω²r e_r − 2ρ ω×W + ∇·τ",
                 "",
                 "Why CFX solves in the rotating frame:",
                 " • blades and hub are fixed → steady problem",
                 " • the frame adds two 'apparent' forces:",
                 "   centrifugal ρω²r (pumps gas outward)",
                 "   Coriolis −2ρω×W (loads the blades,",
                 "   creates the pressure/suction sides)",
                 "",
                 "Rothalpy is conserved along a streamline:",
                 "  I = h + W²/2 − U²/2 = const",
                 f"  → static enthalpy rise ≈ (U₂² − U₁²)/2 + (W₁² − W₂²)/2"], fs=10)
figs.append(("FBD-5_rotating_particle", fig))

# ---------- FBD-6 rotor radial FBD
r = D["rotor"]
fig, ax = page("Rotor: radial free-body diagram (gravity, bearings, unbalance, torque)", 6)
X = lambda x: 6 + (x - 80) * 0.165
yb = 45
ax.add_patch(Rectangle((X(85), yb - 1.5), X(632) - X(85), 3, fc="#d5dbdb", ec=INK))
ax.add_patch(Rectangle((X(300), yb - 3), X(470) - X(300), 6, fc="#aed6f1", ec=INK)); ax.text(X(385), yb + 4.2, "PM motor rotor", ha="center", fontsize=9)
for xi, lab in ((116.7, "imp 1"), (173.7, "imp 2")):
    ax.add_patch(Rectangle((X(xi) - 1.5, yb - 6), 3, 12, fc="#f9e79f", ec=INK)); ax.text(X(xi), yb + 7, lab, ha="center", fontsize=8.5)
ax.add_patch(Rectangle((X(570), yb - 5), X(580) - X(570), 10, fc="#d5dbdb", ec=INK)); ax.text(X(575), yb + 6, "thrust disk", ha="center", fontsize=8.5)
for xb, lab, R in ((r["xA"], "A (front radial brg)", r["RA"]), (r["xB"], "B (rear radial brg)", r["RB"])):
    ax.add_patch(Polygon([(X(xb), yb - 1.5), (X(xb) - 2.5, yb - 8), (X(xb) + 2.5, yb - 8)], fc="white", ec=INK))
    arrow(ax, X(xb), yb - 20, X(xb), yb - 8.5, BLUE, ms=16); ax.text(X(xb), yb - 23, f"R = {R:.1f} N", ha="center", color=BLUE, fontsize=10)
    ax.text(X(xb), yb - 26.5, lab, ha="center", fontsize=8.5)
arrow(ax, X(r["x_cg"]), yb + 18, X(r["x_cg"]), yb + 1.6, RED, ms=16)
ax.text(X(r["x_cg"]) + 1, yb + 15, f"W = mg = {r['W']:.1f} N\n(at CG, x = {r['x_cg']:.0f} mm)", color=RED, fontsize=10)
arrow(ax, X(385), yb - 3, X(385) + 6, yb - 12, PUR, ms=14); ax.text(X(385) + 6.5, yb - 13, f"unbalance F = m e ω² ≈ {r['F_unb']:.0f} N\n(rotating, G2.5)", color=PUR, fontsize=9.5)
ax.annotate("", xy=(X(r["xB"]), 18), xytext=(X(r["xA"]), 18), arrowprops=dict(arrowstyle="<->", color=GRY))
ax.text((X(r["xA"]) + X(r["xB"])) / 2, 19, f"bearing span {r['span']:.0f} mm", ha="center", fontsize=9, color=GRY)
eqs(ax, 6, 82, [f"ΣF_y = 0:  R_A + R_B = W = {r['m']:.2f} kg × 9.81 = {r['W']:.1f} N",
                f"ΣM_A = 0:  R_B (x_B − x_A) = W (x_CG − x_A) → R_B = {r['RB']:.1f} N, R_A = {r['RA']:.1f} N",
                f"Unbalance (ISO 1940 G2.5): e = G/ω = {r['e_um']:.2f} μm → F = m e ω² = {r['F_unb']:.0f} N (rotates at 1×)",
                f"Torque balance (steady):  T_motor = T_aero = {D['power']['torque']:.1f} N·m"], fs=9.5, title="")
figs.append(("FBD-6_rotor_radial", fig))

# ---------- FBD-7 axial thrust
t = D["thrust"]
fig, ax = page("Impellers: axial free-body diagram (pressure thrust, momentum, axial bearing)", 7)
for i, (xx, key, lab) in enumerate(((25, "s1", "Stage-1 impeller"), (58, "s2", "Stage-2 impeller"))):
    ax.add_patch(Polygon([(xx, 30), (xx, 60), (xx + 6, 60), (xx + 6, 30)], fc="#f9e79f", ec=INK)); ax.text(xx + 3, 63, lab, ha="center", fontsize=10.5, weight="bold")
    th = t[key]
    arrow(ax, xx - 12, 50, xx - 0.4, 50, BLUE, ms=16); ax.text(xx - 13, 52, f"F_front = {th['F_front']/1e3:.2f} kN\n(open side, p̄ ≈ (p_eye+p₂)/2)", fontsize=8.5, color=BLUE)
    arrow(ax, xx - 12, 38, xx - 0.4, 38, GRN, ms=14); ax.text(xx - 13, 34.5, f"inlet momentum\nρCm₁²A = {th['F_mom']:.0f} N", fontsize=8.5, color=GRN)
    arrow(ax, xx + 18, 45, xx + 6.4, 45, RED, ms=16); ax.text(xx + 7.5, 47, f"F_back = {th['F_back']/1e3:.2f} kN\n(back face at p₂)", fontsize=8.5, color=RED)
    ax.text(xx + 3, 26, f"net = {th['F_net']/1e3:.2f} kN → suction", ha="center", fontsize=9.5, weight="bold")
ax.add_patch(Rectangle((88, 35), 3, 20, fc="#d5dbdb", ec=INK)); ax.text(89.5, 57, "thrust disk", ha="center", fontsize=9)
arrow(ax, 78, 45, 87.6, 45, PUR, ms=18); ax.text(76, 40, f"F_axial brg ≈ {t['total']/1e3:.2f} kN\n(reaction, toward motor)", color=PUR, fontsize=10, weight="bold")
ax.text(5, 70, "← suction end (−X)                                                                                                  motor end (+X) →", fontsize=9, color=GRY)
eqs(ax, 5, 20, [f"Stage 1: p_eye = {t['p_eye1']:.0f} kPa, p₂ = {t['p_ex1']:.0f} kPa;   Stage 2: p_eye = {t['p_eye2']:.0f} kPa, p₂ = {t['p_ex2']:.0f} kPa",
                f"ΣF_x = 0:  F_axial = Σ(F_back − F_front − ρCm₁²A) = {t['total']/1e3:.2f} kN (net push toward suction; ESTIMATE)",
                "Real machines cut this with labyrinth seals / balance holes / back-to-back cavities; the axial bearing takes the rest."], fs=9.5, title="")
figs.append(("FBD-7_axial_thrust", fig))

# ---------- FBD-8 rotating disc element
st_ = D["stress"]
fig, ax = page("Impeller disc: differential element under centrifugal load (overspeed check)", 8)
cx, cy = 30, 20
ax.add_patch(Wedge((cx, cy), 48, 62, 92, width=16, fc="#f9e79f", ec=INK, lw=1.5))
ax.text(cx + 8, cy + 38, "dθ", fontsize=11)
arrow(ax, cx + 32 * math.cos(math.radians(77)), cy + 32 * math.sin(math.radians(77)), cx + 26 * math.cos(math.radians(77)), cy + 26 * math.sin(math.radians(77)), BLUE)
ax.text(cx - 1, cy + 27, "σ_r", color=BLUE, fontsize=11)
arrow(ax, cx + 48 * math.cos(math.radians(77)), cy + 48 * math.sin(math.radians(77)), cx + 55 * math.cos(math.radians(77)), cy + 55 * math.sin(math.radians(77)), BLUE)
ax.text(cx + 14, cy + 55, "σ_r + dσ_r", color=BLUE, fontsize=11)
for a, sgn in ((62, -1), (92, 1)):
    xm, ym = cx + 40 * math.cos(math.radians(a)), cy + 40 * math.sin(math.radians(a))
    dx, dy = -math.sin(math.radians(a)) * 7 * sgn, math.cos(math.radians(a)) * 7 * sgn
    arrow(ax, xm, ym, xm + dx, ym + dy, RED)
ax.text(cx + 27, cy + 32, "σ_θ", color=RED, fontsize=11); ax.text(cx - 8, cy + 41, "σ_θ", color=RED, fontsize=11)
arrow(ax, cx + 39 * math.cos(math.radians(77)), cy + 39 * math.sin(math.radians(77)), cx + 46 * math.cos(math.radians(77)) + 4, cy + 46 * math.sin(math.radians(77)) - 3, PUR)
ax.text(cx + 24, cy + 52, "body force ρω²r · (r dθ dr t)", color=PUR, fontsize=10.5)
ax.plot([cx], [cy], "k+", ms=10); ax.text(cx - 3, cy - 3, "axis", fontsize=9)
eqs(ax, 60, 72, ["Radial equilibrium of the element:",
                 "  d(r σ_r)/dr − σ_θ + ρω²r² = 0",
                 "Solution, flat disc with bore r_b (plane stress):",
                 "  σ_θ,max (at bore) = (3+ν)/4 · ρω² [r₂² + (1−ν)/(3+ν) r_b²]",
                 f"7075-T6: ρ = {st_['rho']:.0f} kg/m³, ν = {st_['nu']}, S_y = {st_['Sy']:.0f} MPa",
                 f"r₂ = 51.7 mm, r_b = {st_['rb_mm']:.0f} mm",
                 f"30,000 rpm:      σ_θ = {st_['s_design']:.0f} MPa",
                 f"34,500 rpm (115 %): σ_θ = {st_['s_115']:.0f} MPa → SF = {st_['SF']:.1f}",
                 f"39,000 rpm (max): σ_θ = {st_['s_max']:.0f} MPa",
                 "Blades add load at the hub → confirm with FEA."], fs=10)
figs.append(("FBD-8_disc_stress", fig))

with PdfPages(OUT / "FBD_set.pdf") as pdf:
    for name, fg in figs:
        fg.savefig(OUT / f"{name}.png", dpi=130)
        pdf.savefig(fg)
        plt.close(fg)
print("ok", len(figs))
