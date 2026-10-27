# Manufacturing and CAM plan for the impellers

This is a paper study of how the two impellers would be made: a turned blank, then
5-axis milling of the blades and hub from solid. It goes with the drawings in
`drawings/Manufacturing_drawing_set.pdf`:

| Sheet | Content |
|---|---|
| MFG-101 / MFG-102 | Stage-1 / stage-2 machining drawings: datums, GD&T, inspection plan |
| MFG-110 | Blank, turning operations, 5-axis fixture |
| MFG-120 | 5-axis CAM plan: operations, tools, tool-access and flank-milling checks |

The numbers come from `scripts/cam_analysis.py`, which reads the same blade geometry as
the CAD curves (`impeller_geometry.stage_blades`). It writes `docs/cam_summary.json`.
Everything is a first-order planning estimate. Once real toolpaths exist, the CAM
system's collision check, swarf-error report and simulated cycle time replace them.

```bash
python scripts/impeller_geometry.py && python scripts/cam_analysis.py && python scripts/make_mfg_drawings.py
```

> This is a reverse-engineered study model. Don't spin a part made from it without a
> stress review (115 % overspeed), a containment enclosure and a balance check.

---

## 1. Process route

| OP | Machine | Work | Why |
|---|---|---|---|
| 10 | Saw | Ø110 bar 7075-T651 to 52 mm. Ultrasonically inspected stock | Rotating part: no internal flaws |
| 20 | CNC lathe | Face eye side; turn the blade-tip (shroud) envelope +0.1 and tip OD +0.2; drill and rough bore Ø17 | Removes most of the metal cheaply |
| 30 | CNC lathe | **One setup:** face back face A, finish bore B Ø18 H7, finish tip OD and tip envelope | A and B perpendicular, and tip runout tied to them |
| 40 | 5-axis mill | Hub and blades from solid (section 4) | Creates datum C (blade 1) |
| 50 | Bench | Deburr; hand-blend leading edges to 2:1 ellipses | Machined LEs end up blunt or with burrs |
| 60 | CMM / blue-light scan | Inspection plan on MFG-10x | Blade profile vs CAD |
| 70 | Balancer | Two-plane balance, ISO 21940-11 G1.0 | Magnetic-bearing rotor |
| 80 | Spin pit | 115 % speed (34,500 rpm); re-measure bore and tip OD; final balance | Proves the part and settles any yield |

**Why the blade-tip contour is turned and not milled:** the 0.30 mm running clearance is
set by the blade-tip line. A lathe cuts that revolved contour in the same setup as datums
A and B, which gives much better runout than 5-axis milling. In OP40 the milling tools
never touch the tip line; the tops of the blades are already finished.

## 2. Datums and tolerances (MFG-101/102)

- **A**: back face (primary, flatness 0.005). **B**: bore Ø18 H7, perpendicular to A
  within Ø0.005. **C**: main blade 1 (angular orientation, created in OP40 and marked).
- Tip OD Ø103.37 ±0.02 with runout 0.010 to A|B. The blade-tip line has profile 0.05
  to A|B, which holds the clearance to 0.30 +0.05 against a casing made to similar
  accuracy.
- Blade surfaces: profile 0.08 to A|B|C. Blade spacing: position 0.10. Hub flow
  surface: profile 0.10.
- Flow surfaces Ra ≤ 0.8 µm; bore and face A Ra 0.4.
- **Blade thickness 2.0 mm at the hub, 1.0 mm at the tip**, as used in the CFD.
  `02_solidworks_build_guide.md` approximates the blades with a constant-thickness
  Thicken. For a part you intend to machine, build the tapered thickness and **measure
  it in the CAD model** before exporting to CAM.

## 3. Workholding (MFG-110)

The impeller sits face A down on a riser, located by a Ø18 g5 pilot in bore B. It is
clamped by an M8 screw and a Ø22 washer on the eye face. The washer has to be smaller
than the hub at the eye (Ø25.9 on stage 2) so the tools can reach the inducer. The riser
(Ø40 × 60) lifts the part so the holder clears the pallet at 90° tilt. There's no dowel:
OP40 probes the tip OD and face A and starts blade 1 at 0°, which defines datum C.

## 4. Tool access and toolpath strategy

### Where it gets tight

| Check | Stage 1 | Stage 2 |
|---|---|---|
| Tightest gap at the hub (just behind the splitter LE, m ≈ 0.32) | 5.43 mm | 4.84 mm |
| Blade height there | 17.8 mm | 12.1 mm |
| Reach / diameter for the Ø3 finishing ball | 5.9 | 4.0 |
| Blade height at LE / TE | 20.1 / 8.3 mm | 14.0 / 4.2 mm |
| Metal removed in OP40 | 104 cm³ | 65 cm³ |

The narrowest spot isn't at the impeller exit (b2), which is wide in the blade-to-blade
direction (about 16 mm). It's just behind the **splitter leading edge**, where the passage
halves while the blades are still tall. A Ø5 roughing cutter plus 0.3 mm stock plus
0.5 mm clearance needs 6.6 mm, so it can't get in there. A Ø3 tool fits with about 0.9 mm
each side (MFG-120 section view). Stage 1 is the harder part to machine: its blades are
taller (L/D ≈ 6 for a Ø3), so it needs a **tapered** ball (2–3° per side) for stiffness.

### Flank (swarf) or point milling?

The CAD blade is a ruled surface: straight lines join the hub and shroud camber curves.
A ruled surface can be finished with the side of the cutter (flank or swarf milling) in a
few passes, but only if it is close to **developable**. The surface normal twists along
each straight line by the angle Δφ, and a cylinder of radius R can't follow that exactly.
To first order, the deviation is e ≈ R·(1 − cos(Δφ/2)).

| | Max twist | e, R1.0 | e, R1.5 | Flank finish within 0.05 profile? |
|---|---|---|---|---|
| Stage 1 | 35.6° | 0.048 mm | 0.072 mm | **No.** Point-mill, or redesign for less twist |
| Stage 2 | 23.4° | 0.021 mm | 0.031 mm | **Yes** |

The twist comes from the big difference between hub and tip inlet blade angles (about
34° vs 60° on stage 1). To flank-mill stage 1, the blade would need re-fitting toward a
developable surface, and that change would have to be re-checked in CFD.

### Fillets
TC-101/102 call for R1.0 hub fillets. A R1.0 fillet needs a separate Ø2 pencil tool at
up to 18 mm reach (L/D 9). Changing the fillet to **R1.5** lets the Ø3 finishing ball cut
it as part of the hub pass. That removes an operation and a fragile tool. The fillets
aren't in the CFD; R1.5 in a 4.2 mm stage-2 exit adds a few percent blockage near the
hub. That's a reasonable trade, but it's worth one CFD check.

### Operation sequence (OP40)

| Step | Tool | Strategy | Stock left | Stage 2 min | Stage 1 min |
|---|---|---|---|---|---|
| 1 | T1 Ø5 bull R0.5 | 5-axis adaptive / multiblade roughing, 1 mm step-down | 0.30 | 17 | 28 |
| 2 | T2 Ø3 bull R0.25 | Rest roughing at the splitter LE and in corners | 0.30 | 48 | 71 |
| 3 | T3 Ø3 tapered ball | Semi-finish blades and hub, 0.49 mm stepover | 0.10 | 81 | 104 |
| 4 | T3 | Finish hub, flowline LE→TE, 0.22 mm stepover | 0 | 69 | 69 |
| 5 | T3 | Finish blades, point-milled, 0.22 mm stepover | 0 | 111 | 163 |
| 6 | T4 Ø2 tapered ball | Fillet pencil, **only if R1.0 is kept** | 0 | (12) | (12) |
| 7 | T5 chamfer | Edge break (not the LEs) | – | 2 | 2 |
| | | **Total, R1.5 fillets** | | **≈ 5.5 h** | **≈ 7.3 h** |
| | | Stage 2 with flank-finished blades | | **≈ 3.7 h** | n/a |

Assumptions:
- 15,000 rpm spindle, carbide tools in aluminium;
- finish scallop 4 µm, which is about Ra 0.8;
- a 1.35× factor for 5-axis acceleration, linking and tool changes.

Add CAM programming time: 1–3 days for the first part.

### Good practice (it's also on MFG-120)
- Rough with constant stock. **Finish the hub before the blades**, so the blade root is
  cut against the final floor.
- Finish blades **top-down in 2–3 depth steps**, so uncut metal underneath supports the
  thin (1.0 mm) tip.
- Tool-axis control: lead 3–5°, lean away from the blade, and interpolate the axis
  between hub and shroud so it changes smoothly through the passage.
- Simulate with the full machine, holder and fixture. Check the Ø3 neck against the next
  blade at m ≈ 0.3.

## 5. Doing it in CAM software

Dedicated impeller modules take the hub, the shroud (blade-tip surface), the blades,
the splitters and the fillets, and generate the roughing, hub and blade toolpaths
together. Options:
- **hyperMILL** Impeller/Blisk
- **Mastercam** Blade Expert
- **Siemens NX** Turbomachinery Milling
- **SolidCAM** Multiblade

**Fusion 360** with the Manufacturing Extension has no blade wizard, but it can still do
the job: multi-axis roughing or rest roughing, *Swarf* for flank finishing (stage 2),
and *Multi-axis contour* / *Steep and shallow* with tool-axis control for point
finishing. It's the most accessible option for a student licence.

Workflow:
1. **Model prep (SolidWorks):** build the impeller with the tapered blade thickness and
   R1.5 fillets. Also make a separate surface body for the blade-tip (shroud) revolve.
   Export STEP.
2. **Setup:** put the work coordinate system at the axis on face A, with +Z out through
   the eye. Use the OP30 turned blank as stock, and model the riser, washer and screw as
   fixture bodies.
3. **Tool library:** T1–T5 as on MFG-120, each in its real holder (slim shrink-fit).
4. **Toolpaths:** in the order in the table above. Do the main blades and the splitters
   as separate features.
5. **Simulate:** check for gouges, then compare stock against the model. Every face
   should be within ±0.02 mm before posting.
6. **Post and prove out:** post for the actual machine, dry-run above the part, then cut
   a test part in wax or 6061 first.

## 6. Inspection, balance, spin
- Measure the bore with an air gauge. Check face A and the tip OD on a CMM with the part
  on the mandrel.
- Blue-light scan the blades against CAD, which gives a colour map of profile error.
- Section-cut the scan data for blade thickness at 10 / 50 / 90 % span.
- **Balance:** G1.0 at 30,000 rpm allows an eccentricity of only 0.32 µm, which is about
  **0.07 g·mm** of residual unbalance per impeller (mass about 214–231 g). Balance each
  impeller in two planes, removing metal only at the back rim. Then trim-balance the
  complete rotor.
- **Spin test** at 115 % (34,500 rpm) behind containment. Re-measure the bore and tip OD.
  Permanent growth over 0.01 mm means the part has yielded.

## 7. The 3-D printed model
The display model doesn't need any of the above:
- Export the impeller as STL at 1:1, about 0.01 mm chord tolerance.
- Resin (SLA) printing gives the best blade edges.
- Print eye-up with supports on the flat back face, so the passages stay support-free.
- Blade tips are 1.0 mm thick, which prints fine in standard resin.
- Stage 2 is the better-looking part: it has the narrow exit and tall inducer blades.
- If the printed part will go on a shaft, scale the bore up by +0.1 to +0.2 mm.

## 8. Limits of this plan
- The flank-error estimate uses only the ruling twist. The CAM software's error-minimised
  swarf positioning will report the real number, which is usually lower.
- The tool and feed data are generic values for aluminium. Real cutting data depends on
  the machine, the holder and how far the tool sticks out.
- The fixture and tool reach need checking in full-machine simulation.
- The stress and modal checks (overspeed, blade natural frequencies) aren't done here.
  They come before any part spins.
