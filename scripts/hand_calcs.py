"""
Recompute every hand calculation behind the design, step by step, and write
calcs/hand_calcs.json for the calc-package document and FBD drawings.
Each value here is something you can reproduce with a calculator and a
refrigerant property table (or CoolProp).
"""
import json
import math
from pathlib import Path

import CoolProp.CoolProp as CP

import meanline as M          # reuses the R-513A AbstractState and fast flashes
import layout as L

ROOT = Path(__file__).resolve().parent.parent
DP = json.loads((ROOT / "docs" / "design_point.json").read_text())
S1, S2 = DP["stage1"], DP["stage2"]
st = M.st
out = {}

# ---------------------------------------------------------------- 1. cycle state points
Te, Tc = M.T_EVAP, M.T_COND
P_ev = st(CP.QT_INPUTS, 1, Te)["P"]; P_cd = st(CP.QT_INPUTS, 1, Tc)["P"]
s1 = st(CP.PT_INPUTS, P_ev, Te + M.SUPERHEAT)
liq = st(CP.PT_INPUTS, P_cd, Tc - M.SUBCOOL)
q_evap = s1["h"] - liq["h"]
mdot = M.Q_EVAP / q_evap
Vdot = mdot / s1["rho"]
h2s = st(CP.PSmass_INPUTS, P_cd, s1["s"])["h"]
out["cycle"] = dict(Q_evap_kW=M.Q_EVAP / 1e3, tons=M.TONS, Te_C=Te - 273.15, Tc_C=Tc - 273.15,
                    P_ev_kPa=P_ev / 1e3, P_cd_kPa=P_cd / 1e3, T1_C=s1["T"] - 273.15, h1=s1["h"] / 1e3,
                    s1=s1["s"] / 1e3, rho1=s1["rho"], a1=s1["a"], h4=liq["h"] / 1e3, q_evap=q_evap / 1e3,
                    mdot=mdot, Vdot=Vdot, PR=P_cd / P_ev, PR_stage=math.sqrt(P_cd / P_ev),
                    h2s=h2s / 1e3, dhs_total=(h2s - s1["h"]) / 1e3)

# ---------------------------------------------------------------- 2. stage-1 sizing
N = M.N_RPM; omega = N * 2 * math.pi / 60
beta = math.radians(M.BETA2B_DEG); Z = M.Z_MAIN + M.Z_SPLIT
sigma = 1 - math.sqrt(math.cos(beta)) / Z ** 0.7
sigma7 = 1 - math.sqrt(math.cos(beta)) / M.Z_MAIN ** 0.7
psi = sigma - M.PHI2 * math.tan(beta)
P01mid = S1["P_out"]
dhs_1 = st(CP.PSmass_INPUTS, P01mid, s1["s"])["h"] - s1["h"]
out["stage1"] = dict(N=N, omega=omega, Z=Z, beta2b=M.BETA2B_DEG, sigma=sigma, sigma7=sigma7, phi2=M.PHI2,
                     psi=psi, dh0=S1["work_kJkg"], dhs=dhs_1 / 1e3, eta_stage=M.ETA_STAGE_TT,
                     U2=S1["U2"], D2_mm=S1["D2"] * 1e3, r2_mm=S1["D2"] * 500,
                     Cm2=S1["Cm2"], Ct2=S1["Ct2"], C2=S1["C2"], alpha2=S1["alpha2_deg"], M2=S1["M2abs"],
                     rho2=S1["rho2"], b2_mm=S1["b2"] * 1e3, blockage=M.BLOCKAGE2,
                     D1t_mm=S1["D1t"] * 1e3, D1h_mm=S1["D1h"] * 1e3, hub_ratio=M.HUB_RATIO[0],
                     A1_mm2=math.pi / 4 * (S1["D1t"] ** 2 - S1["D1h"] ** 2) * 1e6, Cm1=S1["Cm1"],
                     rho1=S1["rho1"], U1t=S1["U1t"], W1t=S1["W1t"], M1rel=S1["M1rel"], beta1t=S1["beta1t_deg"],
                     beta1h=S1["beta1h_deg"], P_out_kPa=S1["P_out"] / 1e3, T_out_C=S1["T_out"] - 273.15,
                     PR=S1["PR"], phi=S1["flow_coeff"])
out["stage2"] = {k: S2[k] for k in ("D2", "U2", "b2", "Cm2", "Ct2", "C2", "alpha2_deg", "M2abs", "D1t", "D1h",
                                    "Cm1", "U1t", "W1t", "M1rel", "beta1t_deg", "PR", "rho2", "work_kJkg")}
out["stage2"].update(P_in_kPa=S2["P_in"] / 1e3, P_out_kPa=S2["P_out"] / 1e3, T_in_C=S2["T_in"] - 273.15,
                     T_out_C=S2["T_out"] - 273.15)

# eye static state + exit static states (for thrust)
inl = s1
eye1 = st(CP.HmassSmass_INPUTS, inl["h"] - S1["Cm1"] ** 2 / 2, inl["s"])
def exit_static(inlet_h, inlet_s, s):
    dh = s["work_kJkg"] * 1e3
    P02 = st(CP.HmassSmass_INPUTS, inlet_h + M.ETA_IMP_TT * dh, inlet_s)["P"]
    s02 = st(CP.HmassP_INPUTS, inlet_h + dh, P02)
    return st(CP.HmassSmass_INPUTS, s02["h"] - s["C2"] ** 2 / 2, s02["s"])
ex1 = exit_static(inl["h"], inl["s"], S1)
mid = st(CP.HmassP_INPUTS, inl["h"] + S1["work_kJkg"] * 1e3, S1["P_out"])
eye2 = st(CP.HmassSmass_INPUTS, mid["h"] - S2["Cm1"] ** 2 / 2, mid["s"])
ex2 = exit_static(mid["h"], mid["s"], S2)

# ---------------------------------------------------------------- 3. diffuser, de-swirl, volute
r2, r3 = S1["D2"] / 2, S1["D3"] / 2
Ct3 = S1["Ct2"] * r2 / r3; Cm3 = S1["Cm2"] * (r2 * S1["b2"]) / (r3 * S1["b3"])
out["diffuser"] = dict(r2_mm=r2 * 1e3, r3_mm=r3 * 1e3, b3_mm=S1["b3"] * 1e3, Ct3=Ct3, Cm3=Cm3, C3=math.hypot(Ct3, Cm3),
                       deswirl_in=L.deswirl_angles()[0])
vol, qv = L.volute_sections()
out["volute"] = dict(Q_m3s=qv, K=S2["Ct2"] * r2, sections=[dict(theta=t, d=d, rc=rc) for t, d, rc in vol])

# ---------------------------------------------------------------- 4. power, torque, motor
dh_total = (S1["work_kJkg"] + S2["work_kJkg"]) * 1e3
Pgas = mdot * dh_total; Pshaft = Pgas * (1 + M.MECH_LOSS); Pin = Pshaft / M.MOTOR_VFD_EFF
T = Pshaft / omega
r_rot, L_rot = 0.035, 0.170
out["power"] = dict(dh_total=dh_total / 1e3, P_gas=Pgas / 1e3, P_shaft=Pshaft / 1e3, P_in=Pin / 1e3,
                    kW_ton=Pin / 1e3 / M.TONS, COP=M.Q_EVAP / Pin, torque=T, f_elec=N * 2 / 120,
                    shear_kPa=T / (2 * math.pi * r_rot ** 2 * L_rot) / 1e3, rotor_tip=omega * r_rot,
                    eta_overall=(h2s - s1["h"]) / dh_total)

# ---------------------------------------------------------------- 5. pipes
dis = st(CP.PTINPUTS if hasattr(CP, "PTINPUTS") else CP.PT_INPUTS, P_cd, DP["cycle"]["T_discharge_C"] + 273.15)
A_s = math.pi / 4 * (L.SUCTION_ID / 1000) ** 2; A_d = math.pi / 4 * (L.DISCHARGE_ID / 1000) ** 2
out["pipes"] = dict(ID_s=L.SUCTION_ID, ID_d=L.DISCHARGE_ID, V_s=Vdot / A_s, rho_d=dis["rho"],
                    Q_d=mdot / dis["rho"], V_d=mdot / dis["rho"] / A_d)

# ---------------------------------------------------------------- 6. rotor mass, CG, bearing reactions
rho_st, rho_al = 7800.0, 2810.0
parts = []
for x0, x1, d, name in L.SHAFT:
    m = rho_st * math.pi / 4 * (d / 1000) ** 2 * (x1 - x0) / 1000
    parts.append((name, m, (x0 + x1) / 2))
t0, t1, tod = L.THRUST_DISK
parts.append(("thrust disk", rho_st * math.pi / 4 * ((tod / 1000) ** 2 - 0.04 ** 2) * (t1 - t0) / 1000, (t0 + t1) / 2))
# impellers: approximate solid of revolution volume from the meridional section x 2/3 (blades/hollow)
def imp_mass(x0):
    hub = M  # placeholder to keep namespace tidy
    r2m = L.R2 / 1000; Lm = L.IMP_L / 1000
    vol = math.pi * r2m ** 2 * (L.BACKPLATE_T / 1000) + math.pi * (0.5 * (L.R2 / 1000 + 0.0134)) ** 2 * Lm * 0.35
    return rho_al * vol
for x0, name in ((L.IMP1_X0, "impeller 1"), (L.IMP2_X0, "impeller 2")):
    parts.append((name, imp_mass(x0), x0 + 0.7 * L.IMP_L))
m_tot = sum(m for _, m, _ in parts)
x_cg = sum(m * x for _, m, x in parts) / m_tot
xA = sum(L.RADIAL_BRG_FRONT[:2]) / 2; xB = sum(L.RADIAL_BRG_REAR[:2]) / 2
Wt = m_tot * 9.81
RB = Wt * (x_cg - xA) / (xB - xA); RA = Wt - RB
G = 2.5e-3  # ISO 1940 G2.5 mm/s -> m/s
e = G / omega
F_unb = m_tot * e * omega ** 2
out["rotor"] = dict(parts=[dict(name=n, m=m, x=x) for n, m, x in parts], m=m_tot, x_cg=x_cg, xA=xA, xB=xB,
                    W=Wt, RA=RA, RB=RB, G=2.5, e_um=e * 1e6, F_unb=F_unb, span=xB - xA)

# ---------------------------------------------------------------- 7. axial thrust estimate
def thrust(p_eye, p_exit, rho_eye, Cm1, r_s, r1t, r2_):
    A_face = math.pi * (r2_ ** 2 - r_s ** 2)
    p_front = 0.5 * (p_eye + p_exit)          # crude: pressure on the open (blade) side rises p_eye -> p_exit
    F_back = p_exit * A_face                  # back face sees exit static pressure (no balance holes)
    F_front = p_front * A_face
    F_mom = rho_eye * Cm1 ** 2 * math.pi * (r1t ** 2 - r_s ** 2)  # inlet axial momentum, pushes impeller rearward
    return dict(A=A_face, p_front=p_front, F_back=F_back, F_front=F_front, F_mom=F_mom,
                F_net=F_back - F_front - F_mom)
rs = 0.012
th1 = thrust(eye1["P"], ex1["P"], eye1["rho"], S1["Cm1"], rs, S1["D1t"] / 2, r2)
th2 = thrust(eye2["P"], ex2["P"], eye2["rho"], S2["Cm1"], rs, S2["D1t"] / 2, r2)
out["thrust"] = dict(s1=th1, s2=th2, p_eye1=eye1["P"] / 1e3, p_ex1=ex1["P"] / 1e3, p_eye2=eye2["P"] / 1e3,
                     p_ex2=ex2["P"] / 1e3, total=th1["F_net"] + th2["F_net"], r_s=rs)

# ---------------------------------------------------------------- 8. impeller disc stress (rotating disc with bore)
rho7075, nu, Sy = 2810.0, 0.33, 503e6
rb = L.SHAFT_D_IMP / 2000
def hoop(om):
    return (3 + nu) / 4 * rho7075 * om ** 2 * (r2 ** 2 + (1 - nu) / (3 + nu) * rb ** 2)
om115 = omega * 1.15; om_max = 39000 * 2 * math.pi / 60
out["stress"] = dict(rho=rho7075, nu=nu, Sy=Sy / 1e6, rb_mm=rb * 1e3, s_design=hoop(omega) / 1e6,
                     s_115=hoop(om115) / 1e6, s_max=hoop(om_max) / 1e6, SF=Sy / hoop(om115),
                     U_tip_115=om115 * r2)

# ---------------------------------------------------------------- 9. first critical speed (simply supported shaft)
E = 197e9; d = 0.050; Ls = (xB - xA) / 1000
I = math.pi * d ** 4 / 64; A = math.pi * d ** 2 / 4
w1 = (math.pi / Ls) ** 2 * math.sqrt(E * I / (rho_st * A))
out["critical"] = dict(E=E / 1e9, d=d * 1e3, L=Ls * 1e3, I=I, A=A, w1=w1, rpm1=w1 * 60 / (2 * math.pi),
                       margin=w1 * 60 / (2 * math.pi) / 39000)

# ---------------------------------------------------------------- 10. CFD comparison (stage-1 run 3)
f = "R134a"
p1c, p2c, T1c, T2c, mc, tq = 361340, 668707, 299.954, 322.93, 0.385944, 1.89043
h1c = CP.PropsSI("H", "P", p1c, "T", T1c, f); s1c = CP.PropsSI("S", "P", p1c, "T", T1c, f)
h2c = CP.PropsSI("H", "P", p2c, "T", T2c, f); h2sc = CP.PropsSI("H", "P", p2c, "S", s1c, f)
U2c = omega * r2; Ct2c = 95.2902 * 52.0 / (r2 * 1e3); Cr2c = 45.3262 * 52.0 / (r2 * 1e3)
out["cfd"] = dict(PR=p2c / p1c, dh_T=(h2c - h1c) / 1e3, dh_s=(h2sc - h1c) / 1e3, eta=(h2sc - h1c) / (h2c - h1c),
                  P_pass=tq * omega, dh_tq=tq * omega / mc / 1e3, dh_eu=U2c * Ct2c / 1e3, Ct2=Ct2c, Cr2=Cr2c,
                  sigma=(Ct2c + Cr2c * math.tan(beta)) / U2c, alpha2=math.degrees(math.atan2(Ct2c, Cr2c)),
                  mdot_total=7 * mc, P_total=7 * tq * omega / 1e3, inputs=dict(p1=p1c, p2=p2c, T1=T1c, T2=T2c,
                  m=mc, tq=tq, Ct52=95.2902, Cr52=45.3262))

(ROOT / "calcs").mkdir(exist_ok=True)
(ROOT / "calcs" / "hand_calcs.json").write_text(json.dumps(out, indent=2, default=float))
print(json.dumps({k: out[k] for k in ("cycle", "power", "rotor", "thrust", "stress", "critical")}, indent=1, default=lambda x: round(x, 4))[:4000])
