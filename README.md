# Turbocor-class maglev centrifugal compressor: SolidWorks model and Ansys CFD

A reverse-engineered **study model** of the Danfoss Turbocor two-stage, oil-free,
magnetic-bearing compressor used in the Trane TCAA air-cooled chiller (R-513A, about
110 tons per compressor). It includes dimensioned drawings, CAD-ready 3D curves, and
step-by-step SolidWorks and Ansys guides.

> Not OEM geometry. The impellers, flow path, and volute come from a meanline design
> sized to the TCAA operating point, and everything else is proportioned to the
> TT-family envelope. Good for learning, a class project, or a CFD study. Don't use it
> for manufacturing or service parts.

## Start here
1. **`drawings/Turbocor_drawing_set.pdf`**: 12 A3 sheets (cover, GA section and
   exterior, both impellers, rotor, IGVs, casing flow path, volute, motor, bearings,
   CFD domain). PNG previews sit next to it.
2. **`docs/02_solidworks_build_guide.md`**: part-by-part build order, assembly, export.
3. **`docs/03_ansys_cfd_guide.md`**: TurboGrid → CFX single passage (do this first),
   then the optional full-machine Fluent run.
4. `docs/01_design_basis.md`: what came from the IOM, what's assumed, and the meanline
   results.

## Files
| Path | What |
|---|---|
| `cad_curves/stageN/*.txt` | Impeller hub/shroud meridional lines and blade camber lines for SolidWorks *Curve Through XYZ Points* (mm, local Z = axis) |
| `cad_curves/stageN/*.curve` | The same blades as TurboGrid curve files |
| `cad_curves/stageN/impeller_table.csv` | Blade angle and wrap table (also for BladeGen) |
| `cad_curves/flowpath_hub.txt`, `flowpath_shroud.txt` | Whole gas-path walls, suction to volute (machine X, r) |
| `cad_curves/volute_sections.csv`, `rotor_segments.csv` | Volute sections, shaft steps |
| `docs/design_point.json` | Every computed number (cycle, power, both stages) |
| `scripts/` | Generators (see below) |

## Regenerating everything
```bash
pip install -r requirements.txt
python scripts/meanline.py           # design point  -> docs/design_point.json
python scripts/impeller_geometry.py  # blade curves  -> cad_curves/
cd scripts && python make_drawings.py   # drawing set -> drawings/
```
To change the design (speed, tonnage, condensing temperature), edit the constants at the
top of `scripts/meanline.py` and re-run all three. After a CFD run,
`python scripts/cfd_postprocess.py --p0in … --t0in … --p0out … --t0out …` gives real-gas
PR and efficiency and compares them with the meanline.

## Key numbers (design point)
R-513A, SST 3.5 °C / SDT 51.5 °C, 30 000 rpm, 3.34 kg/s, PR 3.90, about 113 kW shaft.
Impellers Ø103.4 mm (U₂ = 162 m/s), 7 + 7 splitter blades, 40° backsweep.
