# Stage-2 CFD results (CFX single passage, R134a stand-in)

Design point, 30 000 rpm, 3.343 kg/s. Setup as in `03_ansys_cfd_guide.md` section A7.
Run: 1000 iterations, Fluid Flow CFX_001 (25 Oct 2026).

## Headline numbers

Mass-averaged totals at the domain inlet and outlet (the CFX Turbo convention).

| Quantity | CFD | Meanline (`design_point.json`) | Difference |
|---|---|---|---|
| P0 in / out (abs) | 720.6 / 1406 kPa | 720.9 / 1420 kPa | −1.0 % on P0 out |
| **PR tt** | **1.951** | 1.970 | −1.0 % |
| **Work Δh0** | **15.54 kJ/kg** | 16.53 kJ/kg | −6.0 % |
| T0 out (real gas, from Δh0) | 333.2 K | 333.3 K | ≈ 0 |
| **η_tt** (impeller + vaneless diffuser) | **0.90** | 0.90 (impeller assumption) | ≈ 0 |
| Gas power, full wheel | 51.9 kW | ≈ 55 kW | −6 % |
| Mass flow | 3.343 kg/s | 3.343 kg/s | set by the outlet BC |

Reproduce with:
```bash
python scripts/cfd_postprocess.py --fluid r134a --p0in 720.6 --t0in 305.0 --p0out 1406 \
       --dh0 15.537 --mdot 3.343 --stage 2
```

## Work: three independent checks agree

| Source | Work |
|---|---|
| `massFlowAve(Total Enthalpy in Stn Frame)`, outlet − inlet | 15.54 kJ/kg |
| Rotor torque (blade + rotating hub, Out File moment summary): 2.314 N·m/passage × ω / ṁ | 15.23 kJ/kg |
| Euler U2·Cθ2 at r = 52 mm (14.55) + stationary-shroud friction torque × ω / ṁ (0.62) | 15.17 kJ/kg |

The work is the most robust number from the run. About 4 % of the rotor work goes into
shroud (tip-gap) friction rather than swirl.

**Don't use CFD-Post's `Total Temperature in Stn Frame`** for a real-gas run. It gave
T0 out = 330.8 K, about 2 K low, which with PR 1.95 implies η_tt = 1.11. Take T0 from Δh0
through the real-gas property tables instead (the script's `--dh0` option).

## Impeller exit (isosurface Radius = 0.052 m)

| Quantity | CFD | Meanline |
|---|---|---|
| Cθ2 | 89.6 m/s | 101.8 m/s |
| Work coefficient ψ = Cθ2/U2 | 0.552 | 0.627 |
| M2 (absolute) | 0.80 | 0.82 |
| Cm2 (mass-averaged) | 70.5 m/s | 45.5 m/s |
| α2 = atan(Cθ/Cm) | ≈ 52° from radial | 65.9° |

The work shortfall against the meanline is slip: the impeller turns the flow less than the
σ = 0.862 slip model assumed. Cm2 and α2 aren't reliable as single numbers. The mass-averaged
Cm came out *below* the mass-averaged Cr, which can't happen pointwise, so there's reverse
flow through the r2 plane (signed mass-flux weighting subtracts it). Treat α2 as indicative
only and quote ψ for the slip comparison.

## Losses and the averaging uncertainty

Mass-averaged static entropy (relative to the inlet):

| Segment | Δs | ≈ Lost work (T·Δs) |
|---|---|---|
| Impeller (inlet → r = 52 mm) | 5.1 J/kg·K | 1.7 kJ/kg |
| Vaneless diffuser (r = 52 → ~80 mm) | 10.4 J/kg·K | 3.5 kJ/kg |
| Rest of the domain to the outlet | ≈ 0 | ≈ 0 |

So **most of the loss is in the vaneless diffuser, not the impeller.**

The flow leaving the domain is far from uniform: mass-averaged M ≈ 0.68, jet-wake, and
about 5.5 % of the outlet area blocked by backflow. Single-number averages then disagree:

| Method | PR tt | η_tt |
|---|---|---|
| Mass-averaged P0 and Δh0 (standard; also the solver's Prtt monitor, ≈ 1.9) | 1.95 | 0.90 |
| Uniform state rebuilt from averaged static p, T and \|V\| at the outlet | 1.73 | 0.76–0.83 |
| Mass-averaged entropy and Δh0 | 1.64 | 0.67 |

- Mass-averaged P0 is known to read high for non-uniform flow (it leaves out the
  mixing loss still to come).
- The rebuilt state reads low (averaging |V| before squaring loses kinetic energy).
- The entropy figure sits below both, so it's distorted by the hot, low-momentum
  recirculating fluid too. It's useful for *where* the loss is, not for the total.
- Post's P0 also *rises* from r2 (1330 kPa) to r ≈ 80 mm (1385 kPa), which a stationary
  diffuser can't do. Same averaging problem; don't use P0 to split impeller and diffuser
  losses.

**Report:** PR 1.95, Δh0 15.5 kJ/kg, η_tt 0.90 (mass-averaged), with the true mixed-out
performance somewhere in PR ≈ 1.73–1.95.

## Outlet state

| | Value |
|---|---|
| Static p / T | 994.8 kPa / 319.7 K |
| Saturation T at outlet static p | 312.3 K (7.4 K superheat, so the gas-only model holds) |
| Total-to-static PR | 1.38 |
| Mass-averaged Mach | 0.68 |

The short vaneless diffuser leaves a lot of kinetic energy unrecovered. In the real
machine the return channel / volute does that job (or loses it). A vaned diffuser or a
longer domain is the obvious next study.

## Convergence and caveats

- Ran to the 1000-iteration limit. RMS residuals flattened at about 1e-4 (mass) and
  4e-4 (momentum) from about iteration 100, with rates ≈ 1.0. That's a plateau from mild
  unsteadiness (tip vortex, diffuser exit), not divergence.
- Imbalances: mass −0.25 %, energy −0.30 % (above the 0.1 % target; acceptable for a
  plateaued run).
- No property-table clipping in the final run (table 1 kPa–4 MPa, 240–480 K, 200 points).
  Max static T in the domain was 368 K, in a recirculation zone near the shroud and
  diffuser hub.
- Fluid is the R134a Peng-Robinson stand-in, not R-513A.
- Single passage, steady, frozen counter-rotating shroud and diffuser hub; no volute or
  return channel.
