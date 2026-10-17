# SolidWorks build guide

This guide builds the compressor shown in `drawings/Turbocor_drawing_set.pdf`. Every
dimension comes from those sheets or from the generated files in `cad_curves/`. Don't
retype a coordinate table by hand when a curve file exists for it.

Estimated time: about 2 h for the impellers, 1–2 h for the casing/volute, about 2 h for
everything else, and 30 min for the assembly.

---

## 0. Set-up (do this first, it matters)

1. **Tools ▸ Options ▸ Document Properties ▸ Units → MMGS.** The curve files are in
   millimetres. *Curve Through XYZ Points* reads numbers in the document's units, so
   set the units **before** importing anything.
2. Use one coordinate system for every machine part:
   | Machine (drawings) | SolidWorks |
   |---|---|
   | +X: rotor axis, X = 0 at the suction flange face, +X toward the motor | +X |
   | +Z: up | +Y |
   | +Y: horizontal, the side the discharge points to | −Z |

   Sketch axisymmetric parts on the **Front plane** with a horizontal centreline through
   the origin, then revolve about it. If **every** part's origin is the suction-flange
   centre, the assembly reduces to "insert at origin, fix". That's the recommended way.
3. **Impeller exception:** the impeller curve files use a *local* frame (Z = axis, Z = 0
   at the eye). Build the impellers in that frame and position them with mates (step 9).
4. Rotation is right-handed about +X: clockwise when you look from the suction flange.

---

## 1. Impeller, stage 1 (TC-101). Do this one first; it's the hard part

Files: `cad_curves/stage1/`

### 1a. Hub body
1. **Insert ▸ Curve ▸ Curve Through XYZ Points ▸ Browse** and pick `hub_meridional.txt`.
   Set *Files of type* to `*.txt`. The curve lies in the XZ (Top) plane.
2. Repeat for `shroud_meridional.txt`. You'll use it as a reference later.
3. Start a sketch on the **Top plane**:
   - **Convert Entities** on the hub curve.
   - Draw a centreline along the Z axis through the origin. This is the axis of revolution.
   - Close the profile: from the eye end of the hub curve (r = 13.4, z = 0), go down to
     the bore at r = 9.0. Run along z to the back face at z = 31.0 + 3.0 = 34.0, go up to
     r = 51.69, then back to the tip end of the hub curve (r = 51.69, z = 31.0).
4. **Revolve** 360° about the centreline. This gives the disc and hub.

> **Common mistake:** with both curves imported, it's easy to Convert the *shroud* curve
> by accident. That gives a fat solid with a flat eye face out to Ø67, and it buries the
> blades. The hub curve is the one that starts at **r = 13.4** at z = 0
> (`hub_meridional.txt`, first line `13.4000 0.0000 0.0000`). The shroud curve starts at
> r = 33.5. A correct section looks like a slim neck at the eye that flares into the disc.

### 1b. Main blade
1. Import `main_hub_camber.txt` and `main_shroud_camber.txt`. These are the true 3D
   camber lines.
2. **Insert ▸ Surface ▸ Boundary Surface.** Set Direction 1 to the hub camber curve and
   then the shroud camber curve. Leave tangency at *None*. The result is the blade camber
   surface.
3. **Insert ▸ Surface ▸ Extend.** Select the hub-side edge, Distance = 1.5 mm,
   *Same surface*. The blade now pokes slightly into the hub, which guarantees a clean
   merge.
4. **Insert ▸ Boss/Base ▸ Thicken.** Pick the surface, choose *Thicken both sides*, enter
   1.5 mm, and tick **Merge result**. (The drawing calls for 2.0 mm at the hub and 1.0 mm
   at the shroud. A constant 1.5 mm is a good approximation for CAD. For CFD, BladeGen
   or TurboGrid uses the true taper; see the CFD guide.)
5. **Trim the blades (required).** Extend and Thicken leave small slivers sticking out
   past the tip diameter and above the shroud line. Remove them with one **Revolved Cut**
   after patterning (step 1d), with *Feature Scope = All bodies*. Sketch it on the Top
   plane:
   - **Convert Entities** on the imported shroud curve, from (r 33.5, z 0) to
     (r 51.69, z 22.75).
   - Close the region *outside* the impeller with lines:
     (51.69, 22.75) → (51.69, 40) → (60, 40) → (60, −5) → (0, −5) → (0, 0) → (33.5, 0).
     The strip below z = 0 also removes any leading-edge stubs poking upstream of the
     eye plane.
   - Revolve-cut 360° about the Z centreline.

### 1c. Splitter
Repeat 1b with `splitter_hub_camber.txt` and `splitter_shroud_camber.txt`. They're
already rotated half a pitch (25.71°) and start at 30 % of the meridional length.

### 1d. Pattern and finish
1. **View ▸ Temporary Axes** on. **Circular Pattern** the main-blade Thicken feature
   about the revolve axis: 7 instances, Equal spacing. Do the same for the splitter.
2. Fillet blade-to-hub R1.0. If the fillet fails, skip it; it doesn't affect the
   assembly.
3. Hollow the bore: Ø18 H7 through.
4. Do the revolved cut from step 1b-5 now, so it trims all 14 blades.
5. **Verify with Section View** on the Top plane (it must match the TC-101 meridional view)
   and the **Measure** tool:
   | Check | Expected |
   |---|---|
   | Blade tips and disc OD | Ø103.4, flush, nothing proud of it |
   | Hub diameter at the eye face (z = 0) | Ø26.8, a thin ring around the Ø18 bore, **not** a large flat face |
   | Blade leading edge at z = 0 | straight radial line from r 13.4 to r 33.5 |
   | Blade height at the trailing edge | 8.26 mm (z 22.75 → 31.0) |
   | Overall axial length | 34.0 (31.0 + 3.0 backplate) |
   | Wrap (LE to TE of one main blade, seen down the axis) | ≈ 80°, tip trailing the rotation |
   | Splitter LE | ≈ 30 % along the passage, midway between main blades |
   | Side silhouette | tall, trumpet-shaped hub rising from the disc to the eye, not a flat dish |
6. Material: 7075-T6 aluminium.

> **If Boundary Surface twists or fails:** use **Loft (surface)** between the two curves
> with *Start/End constraints = None*. You can also cut the point files down: keep every
> second line, but always keep the first and last points.

## 2. Impeller, stage 2 (TC-102)
Save stage 1 as a copy and swap in the files from `cad_curves/stage2/`. Edit the
Curve-Through-XYZ features to point at the new files, or rebuild from scratch. Check the
result: eye Ø54.0, hub at eye Ø25.9, b2 = 4.21.

---

## 3. Rotor shaft (TC-103)
1. Front plane: sketch the stepped profile from `cad_curves/rotor_segments.csv`
   (X from / X to / Ø), all in machine coordinates. Revolve it.
2. Split it into bodies for colour if you like: magnets/CFRP Ø70, bearing laminations Ø50.
3. Thrust disk: separate part, Ø120 × 10 at X = 570–580.
4. Nose cone/nut: separate part. A half-ellipse 10 mm long × Ø26.8, X = 85–95.
5. Tie-bolt M10 through the impeller stack: optional.

## 4. Inlet housing and IGVs (TC-110)

> **Machine parts use DXF profiles, not XYZ curves.** The gas-path walls have sharp
> corners, which a single *Curve Through XYZ Points* spline can't follow. Every revolved
> casing part therefore has a ready-made **closed DXF profile** in `cad_curves/profiles/`.
> The profiles are in machine coordinates (X along the axis, r up), drawn on the Front
> plane.

**How to import a DXF profile (same for every part in sections 4–5):**
1. New part (MMGS). **Insert ▸ DXF/DWG.** In older versions, use *File ▸ Open*, pick the
   `.dxf`, and choose *Import to existing part*.
2. In the import wizard:
   - Choose **Import to existing part as 2D sketch** and select the **Front plane**.
   - Units: **Millimeters**.
   - Leave the entity origin at **0,0** (don't re-centre).
   - Tick *Merge points*.
3. Check one point with *Measure*. For the inlet, the corner at the flange bore must sit
   at X = 0, Y = 51.0.
4. Edit the sketch and draw a **centreline along the X axis** through the origin. Then
   **Revolve** 360° about it. The profile is already closed, so it revolves directly.

Steps:
1. Import `cad_curves/profiles/inlet_housing.dxf` and revolve it. This gives the flange,
   the body, the Ø102 bore and the contraction to the stage-1 eye (Ø67.6 at X = 95).
2. Check against TC-110: flange Ø210 × 20, body Ø144, Ø208 face at X = 95.
3. Bolt holes: 8 × Ø18 on PCD 180.
4. IGV vane: extrude a NACA 0012 profile, chord 40 mm (generate points with any NACA
   tool, or trace TC-110), span from r = 6 to r = 51. Put the pivot pin Ø6 at 25 % chord,
   X = 40. Circular-pattern it ×8.
5. The sync ring (Ø170) and pin bosses are cosmetic.

## 5. Compressor casing: flow path, diaphragm, de-swirl vanes (TC-120)
Import each profile as in section 4 and revolve it about the X axis:
1. **Compressor casing:** `cad_curves/profiles/compressor_casing.dxf`. This one part holds
   the stage-1 shroud → diffuser-1 shroud wall → crossover outer bend → return-channel
   downstream wall → stage-2 shroud → diffuser-2 shroud wall. Its front face at X = 95
   mates with the inlet housing. The step at X = 160, r = 82 leaves room for the volute
   (section 6).
2. **Diaphragm:** `cad_curves/profiles/diaphragm.dxf`. This covers the diffuser-1 hub
   wall, the crossover inner bend (R4.00) and the return-channel upstream wall, turning
   down to the stage-2 eye. It has 1 mm clearance behind the stage-1 impeller and a Ø25
   labyrinth bore over the interstage sleeve.
3. **Fluid domain (for CFD later):** `cad_curves/profiles/fluid_domain.dxf` is the closed
   gas path from the suction flange to the volute inlet. Revolve it into its own part,
   then subtract the impellers when you get to CFD.
   - `flowpath_walls.dxf` holds just the two open wall lines, for reference.
   - `cad_curves/flowpath/` holds the same walls as separate smooth XYZ curves, plus the
     straight-line coordinates in `README.txt`, if you'd rather build the sketch yourself.
4. **De-swirl vanes (12):** on a plane at X = 137.3 (mid-channel), sketch one vane camber
   line from r = 80.1 at 66.6° from radial to r = 40 at 0° (radial). You can trace the
   1:2 plan on TC-120 or use a 3-point arc. Extrude it mid-plane through the channel width
   (7.43 mm) at 3 mm thick, so it bridges diaphragm to casing. Pattern ×12.
5. **Bearing housing front wall:** the diffuser-2 hub wall at X = 182.83.

## 6. Volute (TC-121)
Easiest way, using a loft through sections:
1. Create 8 reference planes through the X axis at θ = 45°, 90°, … 360°. Measure θ from
   the tongue at the **bottom** (machine −Z), increasing **with rotation**. That's
   clockwise seen from the suction.
2. On each plane, sketch a circle using `cad_curves/volute_sections.csv`: centre at
   radius Rc, axial position X = 180.94, diameter from the table.
3. Add a sketch point at θ = 0 (r = 82.1). **Loft (boss)** from the point through the
   8 circles. Use *Start constraint = None*, and add guide curves if it twists.
4. Discharge: loft from the θ = 360° circle (Ø33.1) to a Ø52.5 circle 140 mm away,
   tangent to the spiral (direction = machine +Y = SolidWorks −Z). Add a DN50 flange
   Ø150 × 18.
5. Join the volute to the diffuser-2 exit with a revolved slot: r 80.1 → 84, width
   3.78 mm, X = 179.05–182.83.
6. **Shell** outward 6 mm, or build the solid casing around the gas loft with
   *Combine ▸ Subtract*.

> For CFD, keep the **gas loft body** (before shelling). It *is* the volute fluid domain.

## 7. Motor (TC-130)
- Housing: revolve the shell (Ø300 OD, 12 wall) from X = 186.8 to 650. Add the rear cover
  (X = 650–668).
- Stator sleeve with the cooling groove: revolve a ring of Ø230 ID; groove 8 × 4,
  pitch 20. Use **Insert ▸ Curve ▸ Helix** (pitch 20, 8 revolutions) and a **Swept Cut**
  with an 8 × 4 rectangle profile.
- Stator: extrude a Ø230/Ø72 ring 160 long (X = 305–465). Cut 24 slots (circular
  pattern) and add end-winding rings (copper colour), 25 long, each end.

## 8. Bearings (TC-140)
- Radial (×2): Ø150 ring, 8 poles with Ø51 pole bore, 50 long. Fronts at X = 230 and 495.
- Axial (×2): Ø150/Ø44 discs, 14 thick, at X = 553–567 and 583–597, each with two
  annular coil grooves.
- Touchdown (×2): bearing pair Ø30.4 / Ø55 × 16 at X = 207 and 603. The
  *Toolbox ▸ Bearings* angular-contact model is fine.

## 9. Externals
Electronics enclosure: a sheet-metal box 500 (X 200–700) × 480 × 105, top at 465 above
the base. Mains-input box: X 668–790. Feet: two pedestals with a 380 mm hole span,
4 × Ø14. See TC-100/2.

---

## 10. Assembly
1. New assembly. Insert each machine-coordinate part with its **origin coincident to the
   assembly origin**, then **Fix**. That covers housing, casing, diaphragm, inlet, volute,
   rotor, bearings, stator, and externals.
2. Impellers: add a **Concentric** mate (impeller bore axis to rotor axis), then a
   **Coincident** or **Distance** mate placing the eye plane (local z = 0) at X = 95.0
   (stage 1) or X = 152.0 (stage 2). Local +Z must point to machine +X, so the eye faces
   the suction. Lock rotation with a third mate (Top plane parallel).
3. Run **Evaluate ▸ Interference Detection**. Expected clearances: impeller tip 0.30 mm,
   mag-bearing gap 0.5 mm, touchdown 0.2 mm, motor gap 1.0 mm. Any *interference* means a
   wrong X position, so recheck against TC-100/1.
4. Make an exploded view and a **Section View** through the Front plane. It should match
   TC-100/1.
5. Create a **"CFD" configuration** with everything suppressed except casing, diaphragm,
   inlet, volute, impellers, nose and spacer. You'll export that configuration.

## 11. Export for Ansys
- **File ▸ Save As ▸ Parasolid (*.x_t)** or **STEP AP214**, from the CFD configuration.
- Don't run *Combine* on everything first; SpaceClaim handles the fluid extraction
  (see `03_ansys_cfd_guide.md`, Path B).
