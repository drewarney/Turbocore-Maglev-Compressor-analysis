const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, BorderStyle, ShadingType, ImageRun, LevelFormat, Footer, PageNumber, TableOfContents,
  PageBreak, Header,
} = require('docx');

const ROOT = '/home/user/Turbocore-Maglev-Compressor-analysis';
const FONT = 'Calibri';
const W = 9360; // content width, DXA (US Letter, 1" margins)

const p = (text, opts = {}) => new Paragraph({
  spacing: { after: 140, line: 276 }, ...opts,
  children: Array.isArray(text) ? text : [new TextRun(text)],
});
const t = (text, o = {}) => new TextRun({ text, ...o });
const todo = (text) => new TextRun({ text: `[TO DO: ${text}]`, highlight: 'yellow', bold: true });
const h1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 160 }, children: [t(text)] });
const h2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 }, children: [t(text)] });
const bullet = (runs) => new Paragraph({ numbering: { reference: 'bullets', level: 0 }, spacing: { after: 80 }, children: Array.isArray(runs) ? runs : [t(runs)] });
const caption = (text) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 240 }, children: [t(text, { italics: true, size: 20, color: '444444' })] });

function image(file, widthIn, captionText) {
  const buf = fs.readFileSync(file);
  const { w, h } = pngSize(buf);
  const wpx = widthIn * 96, hpx = wpx * h / w;
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 }, children: [new ImageRun({ type: 'png', data: buf, transformation: { width: wpx, height: hpx } })] }),
    caption(captionText),
  ];
}
function pngSize(buf) { return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) }; }

function placeholder(text) {
  const b = { style: BorderStyle.DASHED, size: 6, color: '999999' };
  return new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: [W],
    rows: [new TableRow({ children: [new TableCell({
      width: { size: W, type: WidthType.DXA }, borders: { top: b, bottom: b, left: b, right: b },
      shading: { fill: 'F4F6F8', type: ShadingType.CLEAR, color: 'auto' },
      margins: { top: 600, bottom: 600, left: 200, right: 200 },
      children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [todo(text)] })],
    })] })],
  });
}

function table(headers, rows, widths) {
  const border = { style: BorderStyle.SINGLE, size: 4, color: 'BFC7CE' };
  const borders = { top: border, bottom: border, left: border, right: border };
  const cell = (text, head, w) => new TableCell({
    width: { size: w, type: WidthType.DXA }, borders,
    shading: head ? { fill: 'DCE6EC', type: ShadingType.CLEAR, color: 'auto' } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: Array.isArray(text) ? text : [t(String(text), { bold: head, size: 20 })] })],
  });
  return new Table({
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: headers.map((x, i) => cell(x, true, widths[i])) }),
           ...rows.map(r => new TableRow({ children: r.map((x, i) => cell(x, false, widths[i])) }))],
  });
}
const tcap = (text) => new Paragraph({ spacing: { before: 200, after: 80 }, children: [t(text, { bold: true, size: 20 })] });

const dp = JSON.parse(fs.readFileSync(path.join(ROOT, 'docs/design_point.json')));
const s1 = dp.stage1, s2 = dp.stage2, c = dp.cycle, pw = dp.power;
const f = (x, n = 1) => Number(x).toFixed(n);

const body = [];

// ---------------- Title page
body.push(
  new Paragraph({ spacing: { before: 2400, after: 200 }, alignment: AlignmentType.CENTER,
    children: [t('Reverse Engineering and CFD Analysis of a Two-Stage, Oil-Free, Magnetic-Bearing Centrifugal Compressor', { bold: true, size: 40 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 },
    children: [t('A Danfoss Turbocor TTS350-class compressor as used in the Trane TCAA air-cooled chiller', { size: 26, color: '444444' })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [todo('Your name')] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [t('Mechanical Engineering, California Polytechnic State University, San Luis Obispo')] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [todo('Course / advisor, if applicable')] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 1200 }, children: [t('Draft, October 2026')] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [t('Status: draft. Covers the design basis, CAD model, CFD method and the first stage-1 CFD result. Design-point CFD, stage 2, the compressor map and structural analysis are still to come.', { italics: true, size: 20, color: '666666' })] }),
  new Paragraph({ children: [new PageBreak()] }),
);

// ---------------- Abstract + TOC
body.push(
  h1('Abstract'),
  p([t('This report documents the reverse engineering of a two-stage, oil-free, magnetic-bearing centrifugal compressor in the class of the Danfoss Turbocor TTS350, the compressor used in the Trane TCAA air-cooled chiller. With no OEM drawings available, the geometry was derived from a one-dimensional (meanline) design at the chiller\'s operating point, using R-513A at 3.5 °C saturated suction and 51.5 °C saturated discharge, 110 tons per compressor and 30,000 rpm. The design gives a 103.4 mm impeller tip diameter, 7 main and 7 splitter blades with 40° backsweep, and a stage pressure ratio near 1.98. The full compressor was modelled in SolidWorks: inlet guide vanes, both impellers, crossover and de-swirl vanes, volute, permanent-magnet motor, and radial, axial and touchdown bearings. The stage-1 impeller was then analysed with a single-passage RANS simulation in Ansys TurboGrid and CFX. At the simulated operating point (300 K inlet, 2.70 kg/s, 30,000 rpm, R-134a real-gas properties), CFD predicts a total-to-total pressure ratio of 1.85 and an isentropic efficiency of about 0.89. This agrees with the meanline evaluated at the same conditions within 1 % on pressure ratio, 0.1° on exit flow angle and 2–5 % on specific work. Specific work computed three independent ways (total-temperature rise, blade torque and Euler exit swirl) agrees within 3 %.')]),
  p([todo('Update the abstract once the design-point and stage-2 results are in.')]),
  new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 160 }, children: [t('Contents')] }),
  new TableOfContents('Contents', { hyperlink: true, headingStyleRange: '1-2' }),
  p([t('Right-click the table of contents in Word and choose Update Field to fill in page numbers.', { italics: true, size: 18, color: '777777' })]),
  new Paragraph({ children: [new PageBreak()] }),
);

// ---------------- 1 Introduction
body.push(
  h1('1  Introduction'),
  p('Oil-free centrifugal compressors with active magnetic bearings have become a common choice for mid-size chillers. Removing the oil system eliminates oil management, improves heat-transfer surfaces in the heat exchangers, and allows the compressor to run at high, variable speed. The Danfoss Turbocor family is the best-known example. Trane uses Turbocor compressors in its TCAA packaged air-cooled magnetic-bearing chiller.'),
  p('The aim of this project is to understand how such a compressor works by building one in detail and analysing it, starting from public information only. The specific objectives are:'),
  bullet('Derive a physically consistent compressor geometry from the chiller\'s published operating conditions, using a meanline design method.'),
  bullet('Build a complete 3D CAD model of the compressor in SolidWorks, including the aerodynamic flow path, rotor, motor and bearings.'),
  bullet('Analyse the impeller aerodynamics with computational fluid dynamics (CFD) in Ansys, and compare the results with the meanline prediction.'),
  bullet('Document the workflow, the problems encountered and how they were resolved.'),
  p([t('Important limitation: ', { bold: true }), t('the geometry in this report is a representative design that does the same job as the real compressor. It is not Danfoss\'s actual geometry, and the results describe this design, not the commercial product.')]),
);

// ---------------- 2 Background
body.push(
  h1('2  Background: the Trane TCAA chiller and its compressor'),
  p('The Trane installation, operation and maintenance manual for the TCAA chiller (TCA-SVX001C-EN, June 2026) does not contain compressor drawings, but it fixes the main facts the design is built on (Table 1).'),
  tcap('Table 1. Information taken from the Trane TCAA IOM'),
  table(['IOM information', 'How it is used in this project'], [
    ['Compressor models TTS300, TTS350, TGS380', 'Turbocor TT-class size, envelope and speed range'],
    ['Refrigerant R-513A', 'All thermodynamic calculations'],
    ['TCAA220: 165–240 tons on two compressors', 'Design capacity of about 110 tons per compressor'],
    ['Air-cooled condenser', 'High lift: saturated discharge about 51.5 °C (125 °F)'],
    ['Two impellers on one high-speed shaft, the only moving part', 'Two in-line impellers on one overhung rotor'],
    ['Gas path: IGVs, 1st impeller, de-swirl vanes, 2nd impeller, diffuser, volute', 'Layout of the aerodynamic flow path'],
    ['Integrated variable-speed drive with soft start; inverter and SCR heatsinks', 'Electronics enclosure on top of the compressor'],
    ['Liquid refrigerant cools the inverter, SCR and stator grooves, then returns to suction through the motor cavity', 'Helical stator cooling groove; motor cavity vented to suction'],
  ], [4300, 5060]),
  p(''),
  p('The variable-speed drive is central to how the machine works. The chiller is supplied with 60 Hz mains power, which would turn a two-pole motor at only 3,600 rpm. At that speed the impellers would produce a pressure ratio of about 1.01, because pressure rise scales with the square of tip speed. The integrated drive rectifies the mains supply to DC and inverts it at about 500 Hz, which runs the permanent-magnet motor at the design speed of 30,000 rpm. Magnetic bearings make that speed practical, because the rotor never touches its supports and needs no oil.'),
);

// ---------------- 3 Meanline design
body.push(
  h1('3  Meanline design'),
  h2('3.1  Method'),
  p('A meanline (one-dimensional) design sizes each stage from the required mass flow and pressure ratio using velocity triangles and loss correlations at a representative streamline. The calculation was written in Python, with real-gas R-513A properties from CoolProp. R-513A was modelled as a 56/44 % by mass mixture of R-1234yf and R-134a. Both stages share one tip diameter, which was solved so that the two stages together reach condenser pressure. Exit slip was estimated with the Wiesner correlation; the inlet eye was sized to minimise the relative Mach number at the blade tip.'),
  tcap('Table 2. Meanline design inputs'),
  table(['Input', 'Value', 'Reason'], [
    ['Capacity per compressor', `${f(dp.inputs.capacity_tons,0)} tons (${f(dp.inputs.capacity_kW,0)} kW)`, 'TCAA220 split over two compressors'],
    ['Saturated suction / discharge', `${f(dp.inputs.T_evap_C)} °C / ${f(dp.inputs.T_cond_C)} °C`, 'AHRI 550/590 air-cooled conditions'],
    ['Superheat / subcooling', '3 K / 5 K', 'Motor-cooling vapour returns to suction; integral subcooler'],
    ['Design speed', '30,000 rpm', 'Mid-high in the Turbocor range; keeps tip relative Mach below 0.9'],
    ['Impeller / stage efficiency (total-to-total)', '0.90 / 0.80', 'Typical for small backswept impellers with vaneless diffusers'],
    ['Blades', '7 main + 7 splitter, 40° backsweep', 'Common for refrigerant compressors of this size'],
  ], [3000, 2700, 3660]),
  h2('3.2  Results'),
  tcap('Table 3. Meanline results at the design point (R-513A)'),
  table(['Quantity', 'Stage 1', 'Stage 2'], [
    ['Tip diameter D₂', `${f(s1.D2*1000)} mm`, `${f(s2.D2*1000)} mm`],
    ['Tip speed U₂', `${f(s1.U2,0)} m/s`, `${f(s2.U2,0)} m/s`],
    ['Eye tip / hub diameter', `${f(s1.D1t*1000)} / ${f(s1.D1h*1000)} mm`, `${f(s2.D1t*1000)} / ${f(s2.D1h*1000)} mm`],
    ['Exit width b₂', `${f(s1.b2*1000,2)} mm`, `${f(s2.b2*1000,2)} mm`],
    ['Inlet relative Mach number (tip)', f(s1.M1rel,2), f(s2.M1rel,2)],
    ['Flow coefficient φ', f(s1.flow_coeff,3), f(s2.flow_coeff,3)],
    ['Work coefficient ψ', f(s1.psi,2), f(s2.psi,2)],
    ['Exit flow angle α₂ (from radial)', `${f(s1.alpha2_deg)}°`, `${f(s2.alpha2_deg)}°`],
    ['Stage pressure ratio', f(s1.PR,3), f(s2.PR,3)],
  ], [4160, 2600, 2600]),
  p(''),
  p(`Overall, the compressor lifts the refrigerant from ${f(c.P_suction_kPa,0)} kPa to ${f(c.P_discharge_kPa,0)} kPa (pressure ratio ${f(c.PR_total,2)}) at ${f(c.mdot_kg_s,2)} kg/s. The estimated shaft power is ${f(pw.shaft_kW,0)} kW, the electrical input about ${f(pw.input_kW,0)} kW, and the compressor-only efficiency about ${f(pw.kW_per_ton,2)} kW/ton. The discharge temperature is ${f(c.T_discharge_C,0)} °C. These values are in the expected range for an air-cooled oil-free centrifugal chiller.`),
  h2('3.3  Blade geometry'),
  p('The 3D blade shape was generated from the meanline results. The hub and shroud contours are cubic Bézier curves. The blade angle varies smoothly from the inlet flow angle (plus 2° incidence) to the 40° exit angle. The angle distribution was adjusted so that hub and shroud reach the same wrap angle at the trailing edge, about 80° for stage 1, which keeps the trailing edge a straight radial line. Integrating the blade angle along each contour gives 3D camber lines. These were exported both as point files for SolidWorks and as TurboGrid curve files, so the CAD model and the CFD mesh come from identical geometry.'),
);

// ---------------- 4 CAD
body.push(
  h1('4  SolidWorks model'),
  p('The complete compressor was modelled in SolidWorks in a single machine coordinate system: X along the rotor axis, with X = 0 at the suction flange face. Most parts are revolved profiles. The impellers were built from the generated 3D curves: the hub revolved from its meridional curve, each blade made as a boundary surface between hub and shroud camber lines and then thickened, patterned seven times, and trimmed to the shroud contour with a revolved cut.'),
  tcap('Table 4. Main components of the model'),
  table(['Component', 'Key features'], [
    ['Inlet housing and IGVs', 'DN100 suction flange; 8 NACA 0012 vanes, 40 mm chord, adjustable angle'],
    ['Stage-1 and stage-2 impellers', 'Ø103.4 mm, 7 + 7 splitter blades, 7075-T6 aluminium'],
    ['Compressor casing and diaphragm', 'Vaneless diffusers, crossover bend, 12 de-swirl vanes'],
    ['Volute', 'Circular sections growing from zero to Ø33.1 mm; DN50 discharge cone'],
    ['Rotor', '547 mm stepped shaft, PM motor section Ø70 mm with carbon-fibre sleeve, thrust disk'],
    ['Motor', '160 mm stator stack, 24 slots; sleeve with helical refrigerant cooling groove'],
    ['Bearings', 'Two 8-pole radial magnetic bearings, double-acting axial bearing, two touchdown bearings'],
    ['Externals', 'Electronics enclosure, mains input box, mounting feet; envelope about 790 × 480 × 465 mm'],
  ], [3200, 6160]),
  ...image(path.join(ROOT, 'drawings/TC-100-1.png'), 6.5, 'Figure 1. General arrangement section of the compressor (drawing TC-100/1).'),
  placeholder('Insert a SolidWorks screenshot of the finished assembly (section view)'),
  caption('Figure 2. SolidWorks assembly, section view.'),
  ...image(path.join(ROOT, 'drawings/TC-101.png'), 6.5, 'Figure 3. Stage-1 impeller: meridional section, blade definition and view from the inlet (drawing TC-101).'),
  placeholder('Insert a SolidWorks screenshot of the stage-1 impeller'),
  caption('Figure 4. Stage-1 impeller in SolidWorks.'),
);

// ---------------- 5 CFD method
body.push(
  h1('5  CFD method (stage 1)'),
  h2('5.1  Computational domain'),
  p('Because the impeller repeats every 51.4° (seven main blades), only one passage was simulated: one main blade, one splitter and the gas between them. The two cut faces of the slice use rotational periodic boundaries. The domain runs from 20 mm upstream of the eye, through the impeller, to the end of the vaneless diffuser at r = 80.1 mm. The 0.3 mm tip gap between the open blades and the casing is included.'),
  ...image(path.join(ROOT, 'drawings/CFD-001.png'), 6.5, 'Figure 5. Single-passage domain and boundary conditions (drawing CFD-001).'),
  h2('5.2  Mesh'),
  p([t('The mesh was generated in Ansys TurboGrid with the ATM Optimized topology, which wraps a structured hexahedral grid around the main blade and the splitter. Boundary-layer refinement used a factor base of 5, with about 12 cells across the tip gap. Over 99.6 % of cells passed every TurboGrid quality check. Remaining flagged cells (under 0.1 %) were at the blade leading edges. ')
     , todo('final node count for the run with splitters')]),
  h2('5.3  Physics and boundary conditions'),
  tcap('Table 5. CFX setup'),
  table(['Setting', 'Value'], [
    ['Analysis', 'Steady state, rotating frame (30,000 rpm about +Z)'],
    ['Fluid', 'R-134a, real-gas library material (stand-in for R-513A, which was designed as an R-134a drop-in)'],
    ['Turbulence model', 'SST k-ω with automatic wall treatment'],
    ['Reference pressure', '300 kPa'],
    ['Inlet', 'Total pressure 364.3 kPa absolute, total temperature (see 6.1), flow normal to boundary'],
    ['Outlet', 'Mass flow (whole machine) or average static pressure'],
    ['Hub and blades', 'No-slip walls rotating with the impeller'],
    ['Casing and diffuser hub', 'No-slip, counter-rotating (stationary in the absolute frame)'],
    ['Advection / timescale', 'High resolution; auto timescale (conservative)'],
  ], [3000, 6360]),
  h2('5.4  Setup problems found and fixed'),
  p('Several problems were found while getting the simulation to run. They are recorded here because each changed the answer significantly.'),
  tcap('Table 6. Problems encountered'),
  table(['Problem', 'Symptom', 'Fix'], [
    ['Project and solver files stored on a cloud-synced (OneDrive) drive', 'Setup file could not be written; solver could not write results', 'Work on the local drive; archive to OneDrive only at the end'],
    ['Splitter blade missing from the mesh after a project rebuild', 'Only one blade per passage; slip factor 0.76; work about 7 % low', 'Re-added the splitter as Blade 2 in TurboGrid and re-meshed'],
    ['Casing set as a rotating wall', 'Casing spun with the blades; unstable outlet flow late in the run', 'Set the shroud to a counter-rotating wall'],
    ['Diffuser hub rotating with the impeller', 'Angular momentum rose 5 % through the diffuser, which is not physical', 'Split the hub after the trailing edge into a separate counter-rotating wall'],
    ['Missing backups and monitors', 'A run that collapsed at iteration ~800 could not be recovered', 'Backups every 100 iterations; monitors for pressure ratio, outlet temperature and mass flow'],
    ['Inlet total temperature entered as 300 K', 'Run solved at an off-design point (see section 6)', 'Use 279.65 K for the design-point run'],
  ], [2800, 3360, 3200]),
);

// ---------------- 6 Results
const res = [
  ['Inlet total pressure', '361.3 kPa', '—'],
  ['Outlet total pressure', '668.7 kPa', '—'],
  ['Total pressure ratio', '1.851', '1.866'],
  ['Inlet / outlet total temperature', '299.95 / 322.93 K', '299.95 / 323.4 K'],
  ['Mass flow (whole wheel)', '2.70 kg/s', '2.70 kg/s (input)'],
  ['Specific work (total-temperature rise)', '15.9 kJ/kg', '16.3 kJ/kg'],
  ['Isentropic efficiency (total-to-total)', '0.89', '0.88 (assumed)'],
  ['Stage-1 shaft power', '41.6 kW', '—'],
];
body.push(
  h1('6  Stage-1 CFD results'),
  h2('6.1  Operating point'),
  p('The first complete run with the splitter included was solved with an inlet total temperature of 300 K instead of the design value of 279.65 K, and the impeller settled at 2.70 kg/s rather than the design 3.343 kg/s (81 % of design flow). It is therefore an off-design point. To compare like with like, the meanline was re-evaluated at exactly these conditions with the same R-134a properties.'),
  p([t('Convergence: the run stopped at 200 iterations. RMS residuals were about 6 × 10⁻⁶ for mass, 4 × 10⁻⁵ for U-momentum and 1.5 × 10⁻⁴ for V- and W-momentum, flat over the last 100 iterations. '), todo('final mass imbalance from the .out file')]),
  h2('6.2  Overall performance'),
  tcap('Table 7. Stage-1 performance: CFD vs meanline at the same operating point'),
  table(['Quantity', 'CFD', 'Meanline'], res, [4160, 2600, 2600]),
  p(''),
  p('The pressure ratio agrees within 1 %, the outlet temperature within 0.5 K and the specific work within about 2 %. The meanline efficiency was an assumption (0.88), so the pressure-ratio agreement partly reflects that choice. The work and temperature comparisons do not depend on it.'),
  h2('6.3  Energy consistency check'),
  p('The work done on the gas was computed three independent ways. All three agree within 3 %, which shows the simulation is conserving energy correctly.'),
  tcap('Table 8. Specific work from three independent methods'),
  table(['Method', 'How it is computed', 'Specific work'], [
    ['Total-temperature rise', 'Real-gas enthalpy change between mass-averaged inlet and outlet total states', '15.9 kJ/kg'],
    ['Blade torque', 'Torque on one passage × angular speed ÷ passage mass flow (1.890 N·m × 3141.6 rad/s ÷ 0.386 kg/s)', '15.4 kJ/kg'],
    ['Euler equation', 'Tip speed × mass-averaged exit swirl velocity (U₂·Cθ₂)', '15.6 kJ/kg'],
  ], [2400, 4960, 2000]),
  h2('6.4  Impeller exit flow and slip'),
  p('Velocities were extracted on a constant-radius surface at r = 52 mm, just downstream of the blade tips, and corrected back to the tip radius (51.7 mm) assuming constant angular momentum and continuity.'),
  tcap('Table 9. Impeller exit: CFD vs meanline'),
  table(['Quantity', 'CFD', 'Meanline, 14 blades', 'Meanline, 7 blades', 'Earlier CFD, no splitter'], [
    ['Swirl velocity Cθ₂ (m/s)', '95.3', '100.2', '84.7', '87.4'],
    ['Radial velocity Cr₂ (m/s)', '45.3', '47.3', '49.2', '43.1'],
    ['Exit flow angle α₂', '64.6°', '64.7°', '59.9°', '64°'],
    ['Slip factor σ', '0.83', '0.86', '0.78', '0.76'],
  ], [2560, 1500, 1800, 1800, 1700]),
  p(''),
  p('The exit flow angle matches the meanline within 0.1°. The CFD slip factor of 0.83 lies between the Wiesner predictions for 7 and 14 blades, closer to 14. This is the expected trend: splitter blades reduce slip, but less than full-length blades, so treating them as full blades in the Wiesner formula slightly overestimates their benefit. Adding the splitter increased the exit swirl from 87.4 m/s to 95.3 m/s, about 9 % more work, compared with the earlier run in which the splitter was missing from the mesh.'),
  h2('6.5  Flow field'),
  p('The following observations come from blade-to-blade, meridional and blade-loading plots. They were made on the earlier run without the splitter and are to be confirmed on the current run.'),
  bullet('Blade loading at 50 % span builds smoothly and peaks near 90 % of the blade length. A sharp pressure spike at the leading edge indicates moderate incidence; there is no shock.'),
  bullet('The inlet relative Mach number at 90 % span is about 0.85, against 0.88 predicted. No region reaches Mach 1.'),
  bullet('A large low-momentum region forms near the shroud in the rear half of the passage. Together with the strongly non-uniform exit flow (mass-averaged radial velocity well above the area average), this is the classic jet-wake pattern of centrifugal impellers.'),
  bullet('Entropy rises along the shroud, so the losses are concentrated near the casing, consistent with tip leakage and the wake region.'),
  placeholder('Insert relative Mach number, blade-to-blade, at 10 %, 50 % and 90 % span'),
  caption('Figure 6. Relative Mach number in the blade-to-blade view.'),
  placeholder('Insert blade loading chart at 50 % span'),
  caption('Figure 7. Blade loading at 50 % span.'),
  placeholder('Insert meridional entropy (or total pressure) plot'),
  caption('Figure 8. Circumferentially averaged static entropy.'),
  placeholder('Insert ImpExit surface coloured by velocity (jet-wake)'),
  caption('Figure 9. Absolute velocity at the impeller exit (r = 52 mm).'),
);

// ---------------- Remaining work
body.push(
  h1('7  Remaining work'),
  bullet('Design-point stage-1 run: 279.65 K inlet, 3.343 kg/s. Expected PR about 1.94 with R-134a properties.'),
  bullet('Switch the material to a custom R-513A real-gas definition and quantify the difference from R-134a.'),
  bullet('Stage-2 run and the combined two-stage pressure ratio.'),
  bullet('Speed lines at 24,000–33,000 rpm to build a compressor map, including surge and choke limits.'),
  bullet('Optional structural checks: impeller stress at 115 % overspeed and rotor critical speed.'),
  bullet('Conclusions.'),
);

// ---------------- References
body.push(
  h1('References'),
  p('[1] Trane, Installation, Operation, and Maintenance: Packaged Air-Cooled Magnetic Bearing Chiller, Model TCAA, TCA-SVX001C-EN, June 2026.'),
  p('[2] F. J. Wiesner, "A review of slip factors for centrifugal impellers," Journal of Engineering for Power, vol. 89, no. 4, pp. 558–566, 1967.'),
  p('[3] S. L. Dixon and C. A. Hall, Fluid Mechanics and Thermodynamics of Turbomachinery, 7th ed. Butterworth-Heinemann, 2014.'),
  p('[4] R. H. Aungier, Centrifugal Compressors: A Strategy for Aerodynamic Design and Analysis. ASME Press, 2000.'),
  p('[5] I. H. Bell, J. Wronski, S. Quoilin and V. Lemort, "Pure and pseudo-pure fluid thermophysical property evaluation and the open-source thermophysical property library CoolProp," Industrial & Engineering Chemistry Research, vol. 53, no. 6, pp. 2498–2508, 2014.'),
  p('[6] Ansys, Inc., Ansys CFX-Solver Theory Guide and TurboGrid User\'s Guide, Release 2026 R1.'),
);

const doc = new Document({
  creator: 'Draft', title: 'Turbocor-class compressor: reverse engineering and CFD',
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 30, bold: true, font: FONT, color: '1F3A4D' }, paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 25, bold: true, font: FONT, color: '2E5A73' }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: '777777' })] })] }) },
    children: body,
  }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(path.join(ROOT, 'report/Turbocor_Compressor_Report_DRAFT.docx'), b); console.log('written'); });
