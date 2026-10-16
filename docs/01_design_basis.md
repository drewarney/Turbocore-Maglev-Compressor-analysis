# Design basis: where every number comes from

## 1. What the Trane IOM (TCA-SVX001C-EN, June 2026) tells us
The IOM covers the **Trane TCAA packaged air-cooled magnetic-bearing chiller**. It's a
chiller manual, so it has no compressor drawings. It does pin down the machine:

| IOM fact | Used for |
|---|---|
| Compressor models **TTS300 / TTS350 / TGS380** (model-number digits 9–11) | Turbocor TT-class envelope and speed range |
| Refrigerant **R-513A** (General Data table) | All thermodynamics |
| TCAA220 = 165–240 tons on **2** compressors, so about 110 tons each | Design capacity |
| Air-cooled condenser | High lift: SCT ≈ 51.5 °C (125 °F) at 95 °F ambient |
| "Two impellers on a single, high-speed rotating shaft … only moving part" | Two in-line impellers on one overhung rotor |
| Gas path: **IGVs → 1st impeller → de-swirl vanes → 2nd impeller → diffuser → volute → discharge** | Flow-path layout (TC-120/121) |
| Integrated VFD with soft start; inverter and SCR heatsinks | Electronics enclosure on top (TC-100) |
| Liquid refrigerant at condenser pressure → solenoids + fixed orifices behind the service cover → inverter heatsink plate, SCR heatsink, **grooves around the motor stator** → vapour returns to **suction through the motor cavity, cooling the rotor** | Stator cooling groove (TC-130); motor cavity vented to suction |
| Covers named in the removal procedure: Mains Input Cover, Service Side Cover, Backplane I/O (J7), suction flange bolts | Externals layout |
| Fault list: shaft, bearing, motor and inverter temperatures; suction and discharge pressure | Sensor locations noted on TC-140 |

## 2. Public Turbocor TT-family knowledge (not from the IOM)
- Envelope about 790 × 480 × 465 mm, mass about 120–135 kg.
- Speed range roughly 18 000–39 000 rpm. 2-pole permanent-magnet synchronous motor.
- 5-axis active magnetic bearings (2 radial + 1 axial), position sensors, and touchdown
  (backup) bearings.
- Aluminium open impellers in series, facing the same way, at the suction end.

## 3. Meanline design (`scripts/meanline.py`)
| Input | Value | Why |
|---|---|---|
| Capacity | 110 tons (387 kW) per compressor | TCAA220 ÷ 2 |
| SST / SDT | 3.5 °C / 51.5 °C | AHRI 550/590 air-cooled (44 °F LWT, 95 °F ambient) |
| Superheat / subcool | 3 K / 5 K | IOM: motor-cooling vapour returns to suction; integral subcooler |
| Speed | 30 000 rpm | Mid-high in the TT range; keeps inlet M_rel < 0.9 |
| Impeller efficiency η_tt | 0.90 | Typical for a small open, backswept impeller |
| Stage efficiency η_tt | 0.80 | Includes vaneless diffuser, crossover/de-swirl or volute |
| Blades | 7 + 7 splitters, β₂b = 40° backsweep | Common for refrigerant compressors this size |
| Slip | Wiesner | Standard correlation |

Results (both stages use the same tip diameter):

| | Stage 1 | Stage 2 |
|---|---|---|
| Tip diameter D₂ | 103.4 mm | 103.4 mm |
| Tip speed U₂ | 162 m/s | 162 m/s |
| Eye tip / hub Ø | 67.0 / 26.8 mm | 54.0 / 25.9 mm |
| Exit width b₂ | 8.26 mm | 4.21 mm |
| Inlet relative Mach (tip) | 0.88 | 0.73 |
| Flow coefficient φ | 0.102 | 0.053 |
| Work coefficient ψ | 0.63 | 0.63 |
| Pressure ratio | 1.98 | 1.97 |

Overall: PR 3.90 (364 → 1420 kPa), ṁ = 3.34 kg/s, shaft power 113 kW, input about
119 kW, **about 1.08 kW/ton compressor-only**, and discharge at 60 °C. These are in the
right range for an air-cooled oil-free centrifugal chiller.

## 4. What is assumed rather than known
Be upfront about these in a report:
- Blade angle distributions, hub/shroud contours, splitter position, de-swirl vane shape
  and volute shape are **textbook design choices**, not measured.
- Bearing, motor and electronics dimensions are proportioned to fit the envelope and the
  power level, not taken from the OEM.
- Real impeller diameters and speeds may differ. If you find published Danfoss data
  (D₂, speed range, map), change `N_RPM`, `TONS`, or `T_COND` in `meanline.py` and re-run
  all three scripts. The drawings and curves regenerate.
- The single-passage CFD tells you how well **this design** works. It isn't a prediction
  of the real Turbocor's performance.
