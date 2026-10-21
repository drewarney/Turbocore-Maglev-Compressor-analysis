"""
Generate 3-D impeller geometry from docs/design_point.json.

For each stage writes, in cad_curves/stageN/ (all units mm, Z = rotation axis,
flow enters the eye travelling in +Z, rotation is +Z right-hand / counter-clockwise
looking from the inlet back toward the motor):

  SolidWorks  (Insert > Curve > Curve Through XYZ Points > Browse... *.txt)
    hub_meridional.txt        hub line in the XZ plane (revolve for the hub body)
    shroud_meridional.txt     shroud line in the XZ plane (revolve for the shroud/casing)
    main_hub_camber.txt       main-blade camber line on the hub surface
    main_shroud_camber.txt    main-blade camber line on the shroud surface
    splitter_hub_camber.txt   splitter camber line on the hub
    splitter_shroud_camber.txt

  Ansys TurboGrid  (File > Load Curves, units mm, rotation axis Z, Cartesian)
    hub.curve, shroud.curve, main_profile.curve, splitter_profile.curve

  impeller_table.csv          meridional + blade-angle table for drawings / BladeGen
"""
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DP = json.loads((ROOT / "docs" / "design_point.json").read_text())
N_PTS = 41
SPLITTER_START = 0.30          # splitter leading edge at 30 % meridional length
INCIDENCE_DEG = 2.0            # blade inlet angle = flow angle + incidence
T_HUB, T_SHROUD = 2.0, 1.0     # blade thickness, mm (hub / shroud)
AXIAL_LEN_RATIO = 0.30         # impeller axial length / D2
TIP_CLEARANCE = 0.30           # open-impeller running clearance, mm (matches layout.py)
DIFF_RATIO = 1.55              # vaneless diffuser exit radius / tip radius (matches layout.py)
INLET_EXT = 20.0               # TurboGrid inlet extension upstream of the eye, mm


def bezier(p, n=N_PTS):
    t = np.linspace(0, 1, n)[:, None]
    p = np.asarray(p, float)
    return ((1 - t) ** 3) * p[0] + 3 * (1 - t) ** 2 * t * p[1] + 3 * (1 - t) * t ** 2 * p[2] + t ** 3 * p[3]


def meridional(s):
    """Hub and shroud lines as arrays of (z, r) in mm."""
    r1h, r1t, r2 = s["D1h"] * 500, s["D1t"] * 500, s["D2"] * 500
    b2 = s["b2"] * 1000
    L = AXIAL_LEN_RATIO * s["D2"] * 1000
    hub = bezier([(0, r1h), (0.55 * L, r1h), (L, 0.45 * r1h + 0.55 * r2 - 0.15 * (r2 - r1h)), (L, r2)])
    zs = L - b2
    shroud = bezier([(0, r1t), (0.50 * zs, r1t), (zs, r1t + 0.35 * (r2 - r1t)), (zs, r2)])
    return hub, shroud, L


def arc_length(zr):
    d = np.diff(zr, axis=0)
    return np.concatenate([[0], np.cumsum(np.hypot(d[:, 0], d[:, 1]))])


def camber(zr, beta_in, beta_out, start=0.0, bump=0.0):
    """Integrate wrap angle d(theta)/dm = tan(beta)/r along a meridional line.

    beta(m) blends smoothly from inlet to exit angle; `bump` (deg) adds a
    sin(pi*m) term used to make hub and shroud reach the same trailing-edge wrap.
    """
    m = arc_length(zr)
    mn = m / m[-1]
    blend = 3 * mn ** 2 - 2 * mn ** 3
    beta = np.radians(beta_in + (beta_out - beta_in) * blend + bump * np.sin(np.pi * mn))
    r = zr[:, 1]
    dtheta = np.tan(beta) / r
    theta = np.concatenate([[0], np.cumsum(0.5 * (dtheta[1:] + dtheta[:-1]) * np.diff(m))])
    # blades lean against rotation: wrap angle is negative for +Z rotation
    theta = -theta
    keep = mn >= start - 1e-9
    return zr[keep], theta[keep], np.degrees(beta[keep]), mn[keep]


def solve_bump(zr, beta_in, beta_out, target_wrap):
    """Bisect the beta 'bump' so the trailing-edge wrap equals target_wrap (rad, negative)."""
    lo, hi = -30.0, 30.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        wrap = camber(zr, beta_in, beta_out, bump=mid)[1][-1]
        lo, hi = (mid, hi) if wrap > target_wrap else (lo, mid)
    return 0.5 * (lo + hi)


def to_xyz(zr, theta, phase=0.0):
    th = theta + phase
    return np.column_stack([zr[:, 1] * np.cos(th), zr[:, 1] * np.sin(th), zr[:, 0]])


def thick_profile(zr, theta, t_mm, phase=0.0):
    """Closed blade section: offset camber +/- t/2 circumferentially, LE->TE->LE."""
    r = zr[:, 1]
    taper = np.minimum(1.0, np.linspace(0, 1, len(r)) / 0.08)  # rounded-ish leading edge
    dth = 0.5 * t_mm * np.maximum(taper, 0.15) / r
    ss = to_xyz(zr, theta + dth, phase)
    ps = to_xyz(zr, theta - dth, phase)
    return np.vstack([ss, ps[::-1][1:]])


def offset_outward(zr, dist):
    """Offset a shroud line (z, r) by dist along its outward normal (axial at eye, radial at tip)."""
    t = np.gradient(zr, axis=0)
    t /= np.linalg.norm(t, axis=1)[:, None]
    n = np.column_stack([-t[:, 1], t[:, 0]])
    n[0], n[-1] = (0.0, 1.0), (-1.0, 0.0)
    return zr + dist * n


def write_turbogrid(out, s, hub, shroud, L, main_h, main_s, spl_h, spl_s, pitch):
    """TurboGrid inputs: hub/shroud span the whole passage (inlet extension + vaneless
    diffuser to R3); shroud = casing (blade tip + clearance); blade profiles lie ON the
    hub and ON the casing so TurboGrid can cut the tip gap itself. No comment lines."""
    b2 = s["b2"] * 1000
    r2, r3 = shroud[-1, 1], DIFF_RATIO * shroud[-1, 1]
    casing = offset_outward(shroud, TIP_CLEARANCE)
    z_shr_wall = (L - b2) + 0.05 * b2              # diffuser walls pinch to b3 = 0.9 b2
    z_hub_wall = L - 0.05 * b2
    ramp = np.linspace(0, 1, 6)[1:]
    hub_ext = np.vstack([[[-INLET_EXT, hub[0, 1]], [-INLET_EXT / 2, hub[0, 1]]], hub,
                         np.column_stack([L + (z_hub_wall - L) * ramp, r2 + 2.0 * ramp]),
                         np.column_stack([np.full(8, z_hub_wall), np.linspace(r2 + 2.0, r3, 9)[1:]])])
    z_c = casing[-1, 0]
    shr_ext = np.vstack([[[-INLET_EXT, casing[0, 1]], [-INLET_EXT / 2, casing[0, 1]]], casing,
                         np.column_stack([z_c + (z_shr_wall - z_c) * ramp, r2 + 2.0 * ramp]),
                         np.column_stack([np.full(8, z_shr_wall), np.linspace(r2 + 2.0, r3, 9)[1:]])])
    for name, line in (("hub.curve", hub_ext), ("shroud.curve", shr_ext)):
        (out / name).write_text("\n".join(f"{r:.4f} 0.0000 {z:.4f}" for z, r in line) + "\n")
    for name, (h, sh_, ph) in {"main_profile.curve": (main_h, main_s, 0.0),
                                "splitter_profile.curve": (spl_h, spl_s, pitch / 2)}.items():
        zr_s = offset_outward(sh_[0], TIP_CLEARANCE) if len(sh_[0]) == len(shroud) else \
            offset_outward(shroud, TIP_CLEARANCE)[-len(sh_[0]):]
        lines = []
        for k, (zr, th, t) in enumerate(((h[0], h[1], T_HUB), (zr_s, sh_[1], T_SHROUD)), 1):
            lines.append(f"#Profile {k}")
            lines += [f"{x:.4f} {y:.4f} {z:.4f}" for x, y, z in thick_profile(zr, th, t, ph)]
        (out / name).write_text("\n".join(lines) + "\n")


def write_xyz(path, pts):
    path.write_text("\n".join(f"{x:.4f} {y:.4f} {z:.4f}" for x, y, z in pts) + "\n")


def main():
    for i in (1, 2):
        s = DP[f"stage{i}"]
        out = ROOT / "cad_curves" / f"stage{i}"
        out.mkdir(parents=True, exist_ok=True)
        hub, shroud, L = meridional(s)
        cm1 = s["Cm1"]
        omega = DP["inputs"]["speed_rpm"] * 2 * math.pi / 60
        b_in_h = math.degrees(math.atan(omega * s["D1h"] / 2 / cm1)) + INCIDENCE_DEG
        b_in_s = math.degrees(math.atan(omega * s["D1t"] / 2 / cm1)) + INCIDENCE_DEG
        b_out = DP["inputs"]["beta2b_deg"]
        pitch = 2 * math.pi / 7

        # common trailing-edge wrap = mean of the unmodified hub and shroud wraps,
        # so the trailing edge is a straight radial line (no lean / rake)
        target = 0.5 * (camber(hub, b_in_h, b_out)[1][-1] + camber(shroud, b_in_s, b_out)[1][-1])
        bump_h = solve_bump(hub, b_in_h, b_out, target)
        bump_s = solve_bump(shroud, b_in_s, b_out, target)
        zh, th_h, bh, mh = camber(hub, b_in_h, b_out, bump=bump_h)
        zs, th_s, bs, ms = camber(shroud, b_in_s, b_out, bump=bump_s)
        # splitter: same camber, rotated half a pitch, starting at SPLITTER_START
        zhs, th_hs, _, _ = camber(hub, b_in_h, b_out, SPLITTER_START, bump_h)
        zss, th_ss, _, _ = camber(shroud, b_in_s, b_out, SPLITTER_START, bump_s)

        zero = np.zeros(len(hub))
        write_xyz(out / "hub_meridional.txt", np.column_stack([hub[:, 1], zero, hub[:, 0]]))
        write_xyz(out / "shroud_meridional.txt", np.column_stack([shroud[:, 1], zero, shroud[:, 0]]))
        write_xyz(out / "main_hub_camber.txt", to_xyz(zh, th_h))
        write_xyz(out / "main_shroud_camber.txt", to_xyz(zs, th_s))
        write_xyz(out / "splitter_hub_camber.txt", to_xyz(zhs, th_hs, pitch / 2))
        write_xyz(out / "splitter_shroud_camber.txt", to_xyz(zss, th_ss, pitch / 2))

        write_turbogrid(out, s, hub, shroud, L, (zh, th_h), (zs, th_s), (zhs, th_hs), (zss, th_ss), pitch)

        rows = ["m_norm,hub_z_mm,hub_r_mm,hub_beta_deg,hub_wrap_deg,"
                "shroud_z_mm,shroud_r_mm,shroud_beta_deg,shroud_wrap_deg"]
        for k in range(N_PTS):
            rows.append(f"{mh[k]:.3f},{zh[k,0]:.3f},{zh[k,1]:.3f},{bh[k]:.2f},{math.degrees(th_h[k]):.2f},"
                        f"{zs[k,0]:.3f},{zs[k,1]:.3f},{bs[k]:.2f},{math.degrees(th_s[k]):.2f}")
        (out / "impeller_table.csv").write_text("\n".join(rows) + "\n")
        print(f"stage {i}: L={L:.1f} mm  beta_in hub/shroud {b_in_h:.1f}/{b_in_s:.1f} deg, "
              f"wrap hub {math.degrees(th_h[-1]):.1f} shroud {math.degrees(th_s[-1]):.1f} deg, "
              f"beta range hub {bh.min():.1f}-{bh.max():.1f} shroud {bs.min():.1f}-{bs.max():.1f}")


if __name__ == "__main__":
    main()
