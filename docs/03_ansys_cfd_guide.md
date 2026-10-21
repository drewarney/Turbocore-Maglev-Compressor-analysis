# Ansys CFD walkthrough

There are two paths. **Do Path A first.** It's the standard way turbomachinery engineers
analyse an impeller, it fits in student or teaching cell limits, and it converges in an
hour or two. Path B (the full machine) is a stretch goal for once A works.

| | Path A: single passage | Path B: full stage, 360° |
|---|---|---|
| Geometry | BladeGen / TurboGrid curves (`cad_curves/stageN/*.curve`) | SolidWorks assembly (CFD configuration) |
| Mesh | TurboGrid (structured hex) | Fluent Meshing (poly-hexcore) |
| Solver | CFX (Turbo Mode) | Fluent or CFX |
| Cells | 0.3–0.8 M | 8–20 M |
| What you learn | Impeller PR, efficiency, blade loading, speed lines | Volute, de-swirl and crossover losses, interaction |

> **Licence check.** Ansys Student has a problem-size cap (around 1 M cells/nodes for
> CFD), and some university teaching licences cap lower. Path A fits under those caps.
> Path B needs a research licence, which Cal Poly labs usually have on the lab machines.
> Check what your Software Hub install is before you start.

Every boundary-condition number below comes from `docs/design_point.json`. If you change
the design point and re-run `scripts/meanline.py`, refresh these numbers too.

---

## Design-point numbers you'll type in

| Quantity | Stage 1 | Stage 2 |
|---|---|---|
| Inlet total pressure | 364.3 kPa abs | 720.9 kPa abs |
| Inlet total temperature | 279.65 K (6.5 °C) | 305.0 K |
| Mass flow (full wheel) | 3.343 kg/s | 3.343 kg/s |
| Speed | 30 000 rpm | 30 000 rpm |
| Expected PR (meanline) | 1.98 | 1.97 |
| Passages | 7 (main + splitter each) | 7 |

### R-513A material properties (for a custom real-gas material)
R-513A is R-1234yf/R-134a 56/44 wt%, an azeotrope that behaves like a pure fluid.

| Property | Value |
|---|---|
| Molar mass | 108.4 kg/kmol |
| Critical temperature | 369.65 K (96.5 °C) |
| Critical pressure | 3.766 MPa |
| Acentric factor (mass-weighted) | 0.30 |
| Ideal-gas cp (zero pressure) | cp0 ≈ 317.8 + 1.826·T  [J/kg·K], fit 260–360 K |
| Dynamic viscosity (suction) | 1.13 × 10⁻⁵ Pa·s |
| Thermal conductivity (suction) | ≈ 0.013 W/m·K |

**Shortcut for a first run:** use the built-in **R134a Peng-Robinson** material (CFX:
*Material Library ▸ Real Fluid ▸ Peng Robinson ▸ R134a*). R-513A was designed as a drop-in
for R-134a. Expect the first answers within a few percent; then switch to the custom
R-513A material.

---

## PATH A: stage-1 impeller, single passage (CFX)

### A1. Geometry in TurboGrid (Workbench ▸ *TurboGrid* component)
The `.curve` files in `cad_curves/stage1/` are made for TurboGrid:
- `hub.curve` and `shroud.curve` cover the whole passage: a 20 mm straight inlet ahead
  of the eye, the impeller, and the vaneless diffuser out to r = 80.1 mm.
- The shroud is the **casing**, which is the blade tip plus 0.3 mm.
- The blade profiles lie on the hub (`#Profile 1`) and on the casing (`#Profile 2`).
  TurboGrid trims the tip gap itself.

1. **File ▸ Load Curves.**
   - Machine type: *Centrifugal Compressor*
   - Rotation axis: **Z**; length units: **mm**; coordinates: *Cartesian*
   - Hub: `hub.curve`; Shroud: `shroud.curve`
   - Blade: `main_profile.curve`
   - Number of bladesets: **7**
2. Add the splitter: in the Blade Set, set the number of blades to **2** and load
   `splitter_profile.curve` as Blade 2.
3. **Shroud Tip:** set it to *Normal Distance*, **0.30 mm**. **Hub Tip:** *None*.
4. **Inlet / Outlet:** keep them at the start and end of the hub/shroud curves. Those are
   X = −20 mm (inlet) and r = 80.1 mm (diffuser exit).

> **If TurboGrid won't read the profile file:** open it in Notepad. Some versions want a
> plain `#` separator line between profiles instead of `#Profile 1` / `#Profile 2`. The
> fallback is BladeGen: import `impeller_table.csv` (meridional coordinates plus β/θ),
> then *Export TurboGrid Input Files*.

### A2. Mesh
1. Topology: **ATM Optimized** (default). Enable *Splitter* if it asks.
2. Mesh Data:
   - Method: *Target Passage Mesh Size*, **Fine**, about **400 k nodes**. Go up to 800 k
     if your licence allows.
   - Boundary layer refinement: factor 2–3. Aim for **y⁺ ≈ 20–60** on the blades.
     R-513A is dense: first-cell height for y⁺ = 1 would be about 0.1 µm. Use wall
     functions; SST's automatic wall treatment handles them. A first cell of about 5 µm
     gives y⁺ ≈ 40.
   - Tip clearance: at least **10–15 elements** across the 0.3 mm gap.
3. Check **Mesh Analysis.** Minimum face angle should be above 15° and maximum element
   volume ratio below 20. Fix anything red before you go on.

### A3. CFX-Pre (use **Turbo Mode**: *Tools ▸ Turbo Mode*)
1. **Basic settings:** machine type *Centrifugal Compressor*, rotation axis **Z**.
2. **Component:** *R1*, type **Rotating**, **30 000 rpm**. Load the TurboGrid mesh.
   Passages per mesh = 1, passages in 360 = 7.
   - **Rotation sign check:** the blades were generated for **positive** rotation about
     +Z (right-hand rule). If your first solution gives PR < 1 or reversed blade loading,
     flip the sign.
3. **Physics:**
   - Fluid: R134a PR (first run), then custom R-513A.
   - Analysis: steady state.
   - Heat transfer: **Total Energy**. Turbulence: **SST**.
   - Reference pressure: **300 kPa**. Every pressure you type below is *relative* to it.
   - Inlet: **P-Total**, relative total pressure = 64.26 kPa (that's 364.26 kPa abs),
     T-Total = 279.65 K, flow direction *normal to boundary*. Zero swirl means IGV fully
     open.
   - Outlet: **Mass Flow Rate = 3.343 kg/s**, *Total for all sections*.
4. **Interfaces:** Turbo Mode creates the **rotational periodic** pair automatically.
   Check that it says *Rotational Periodicity, 51.43°*.
5. **Boundaries:** hub = rotating no-slip wall. Shroud = **counter-rotating wall**
   (stationary in the absolute frame). Turbo Mode asks for this; tick it.
6. **Solver control:**
   - Advection: *High Resolution*. Timescale: *Auto*, Conservative, factor 1.
   - Iterations: 1000 maximum. Residual target **RMS 1e-5**.
7. **Initialisation:** Automatic, or set a velocity of about 60 m/s axial and a pressure
   of about 100 kPa relative. A good initial guess helps real-gas runs a lot.

### A4. Run (CFX-Solver Manager)
- Use *Intel MPI Local Parallel*, 4–8 cores. Expect 1–2 h for 400 k nodes.
- Add **monitors** (Output Control ▸ Monitor ▸ Expression) and watch them flatten:
  ```
  PRtt  = massFlowAve(Total Pressure in Stn Frame)@R1 Outlet / massFlowAve(Total Pressure in Stn Frame)@R1 Inlet
  T0out = massFlowAve(Total Temperature in Stn Frame)@R1 Outlet
  ```
- **Converged** means: RMS residuals ≤ 1e-5 (1e-4 is acceptable), mass imbalance below
  0.1 %, and PR/T0 flat for at least 100 iterations.
- If it diverges early: drop the timescale factor to 0.5. Start with a lower mass flow,
  or run the first 100 iterations with the R134a PR material.

### A5. Post-processing (CFD-Post: *Turbo* tab ▸ Initialise All Components)
1. Read mass-averaged **total pressure and total temperature in the stationary frame**
   at the inlet and outlet. Then run:
   ```bash
   python scripts/cfd_postprocess.py --p0in 364.26 --t0in 279.65 \
          --p0out <from CFD> --t0out <from CFD> --mdot 3.343 --stage 1
   ```
   This gives the real-gas PR and η_tt and compares them with the meanline (PR 1.98,
   work 16.5 kJ/kg). **Within 5–10 % = good.** Bigger gaps usually mean a wrong rotation
   sign, too coarse a tip-gap mesh, or a wrong reference pressure.
2. Standard plots:
   - **Blade-to-blade** at 10/50/90 % span: relative Mach number. Look for the LE shock
     near the shroud; inlet M_rel is about 0.88 at the tip.
   - **Blade loading** chart: pressure vs. streamwise location at 50 % span.
   - **Meridional** averaged entropy or total pressure. Tip-leakage losses show up near
     the shroud.
   - Streamlines from the tip gap.
3. Exit flow angle: compare with the meanline α₂ ≈ 66° from radial at the impeller exit
   (r = 51.7 mm).

### A6. Speed lines (the "map")
For each speed (24k, 27k, 30k, 33k rpm):
1. Start near design. **Change the outlet to Static Pressure** (average); it's more
   stable near choke. Step the back-pressure up and down.
2. **Choke:** mass flow stops increasing as you lower the back-pressure.
3. **Surge (approximate):** steady RANS will stop converging, or PR peaks and falls, as
   you raise the back-pressure. The last converged point is your numerical surge limit.
4. Plot PR and η_tt against corrected mass flow. That's a compressor map, the same kind
   of picture Danfoss publishes for the TT series.

### A7. Stage 2
Repeat with `cad_curves/stage2/*` and inlet P0 = 720.9 kPa abs (reference pressure about
600 kPa), T0 = 305.0 K. For a true two-stage run, add both as components in Turbo Mode
with a **Stage (mixing-plane)** interface. The de-swirl/crossover isn't in the TurboGrid
geometry, though, so stage-by-stage is the clean way to do it.

---

## PATH B: full compressor (stretch goal)

### B1. Fluid volume in SpaceClaim (or DesignModeler)
1. Import the **CFD configuration** export (`.x_t` / `.step`).
2. Cap the suction and discharge flange faces with surfaces. Then use **Prepare ▸ Volume
   Extract**: pick the inside faces, and SpaceClaim fills the gas path.
3. Delete the solids. Keep only the fluid volume.
4. Split the fluid into zones with **cylinders/planes** at:
   - impeller-1 inlet (X = 90) and exit (r = 53)
   - impeller-2 inlet (X = 147) and exit (r = 53)

   You end up with **rotating zones** around each impeller and **stationary zones** for
   inlet, diffuser/crossover/de-swirl and volute. Use **Share Topology**.
5. Name the selections: `inlet`, `outlet`, `wall_shroud1`, `wall_hub1`, `blade1`, …,
   `int_*` for the interfaces.

### B2. Mesh (Fluent Meshing, *Watertight Geometry* workflow)
- Local sizing: blades 0.3–0.5 mm, tip gap 0.05 mm (3+ cells), volute 1.5 mm.
- Boundary layers: 5–8 layers on the walls, first layer about 5 µm.
- Volume fill: **poly-hexcore**. Expect 8–20 M cells.

### B3. Fluent setup
- Pressure-based coupled solver, steady. Energy on. k-ω SST.
- Material: **Real gas ▸ Peng-Robinson**, entering the R-513A constants above. Or use the
  NIST real-gas (REFPROP) model with the R-513A mixture file, if your install has it.
- Cell zones: impeller zones get **Frame Motion**, 3141.6 rad/s about **+X** (the machine
  axis in the SolidWorks export). Stationary zones get nothing.
- Interfaces: **Frozen Rotor** (mesh interfaces between rotating and stationary zones).
- Inlet: pressure inlet, P0 = 364.26 kPa abs (with operating pressure = 0, or set the
  operating pressure and use gauge values), T0 = 279.65 K. Outlet: mass-flow outlet,
  3.343 kg/s, or pressure outlet at about 1420 kPa.
- Ramp the speed up over the first few hundred iterations, or initialise from a 15 000 rpm
  solution.
- Monitors: mass-weighted P0 and T0 at the inlet, at `int_imp1_out`, at `int_imp2_in` and
  at the outlet. Use them to split losses: impeller 1 / crossover + de-swirl / impeller 2 /
  volute.

### B4. What to compare
- Overall PR should reach about 3.9 (discharge 1420 kPa) at 30 000 rpm, 3.34 kg/s.
- The meanline expects about 111 kW gas power and an overall η about 0.79.
- Volute circumferential static-pressure distortion at design should be fairly flat.
  Off-design it grows. Try 70 % and 120 % flow.

---

## Optional extras that make a strong project
1. **Ansys Mechanical, Modal:** rotor first bending critical with the mag bearings as
   springs (k ≈ 1–3 × 10⁶ N/m). It must sit above about 47 000 rpm, which is 1.2 × the
   39 000 rpm maximum.
2. **Static Structural:** impeller stress at 115 % overspeed (34 500 rpm), centrifugal
   load only, 7075-T6. Peak von Mises should stay below 0.6 × yield.
3. **IGV study:** add the IGV row as a stationary component and rerun Path A with the
   vanes at 30°/50°. This shows the part-load prewhirl capacity control the IOM describes.
4. **Validation sanity check:** a Turbocor TTS350-class compressor at these conditions
   draws about 110–125 kW. The meanline gives 119 kW input. If your CFD efficiency gives
   a power far outside that band, something is off.
