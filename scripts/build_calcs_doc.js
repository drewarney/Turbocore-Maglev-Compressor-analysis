const fs = require('fs'), path = require('path');
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType,
  BorderStyle, ShadingType, ImageRun, LevelFormat, Footer, PageNumber, TableOfContents, PageBreak } = require('docx');
const ROOT = '/home/user/Turbocore-Maglev-Compressor-analysis';
const D = JSON.parse(fs.readFileSync(path.join(ROOT, 'calcs/hand_calcs.json')));
const DP = JSON.parse(fs.readFileSync(path.join(ROOT, 'docs/design_point.json')));
const f = (x, n = 2) => Number(x).toLocaleString('en-US', { minimumFractionDigits: n, maximumFractionDigits: n });
const W = 9360;
const t = (text, o = {}) => new TextRun({ text, ...o });
const P = (runs, o = {}) => new Paragraph({ spacing: { after: 100, line: 276 }, ...o, children: Array.isArray(runs) ? runs : [t(runs)] });
const EQ = (text) => new Paragraph({ spacing: { after: 60 }, indent: { left: 540 }, children: [t(text, { font: 'Cambria Math', size: 22 })] });
const bullet = (text) => new Paragraph({ numbering: { reference: 'b', level: 0 }, spacing: { after: 40 }, children: [t(text)] });
const H1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: false, spacing: { before: 360, after: 140 }, children: [t(text)] });
const label = (text) => new Paragraph({ spacing: { before: 120, after: 40 }, children: [t(text.toUpperCase(), { bold: true, size: 18, color: '2E5A73' })] });
function result(text) {
  const b = { style: BorderStyle.SINGLE, size: 8, color: '2E5A73' };
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [W], rows: [new TableRow({ children: [new TableCell({
    width: { size: W, type: WidthType.DXA }, borders: { top: b, bottom: b, left: b, right: b },
    shading: { fill: 'EAF2F7', type: ShadingType.CLEAR, color: 'auto' }, margins: { top: 80, bottom: 80, left: 140, right: 140 },
    children: (Array.isArray(text) ? text : [text]).map(x => new Paragraph({ children: [t('Result:  ', { bold: true }), t(x, { bold: true })] })) })] })] });
}
function img(file, widthIn, cap) {
  const buf = fs.readFileSync(file); const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  return [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 }, children: [new ImageRun({ type: 'png', data: buf, transformation: { width: widthIn * 96, height: widthIn * 96 * h / w } })] }),
          new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [t(cap, { italics: true, size: 18, color: '555555' })] })];
}
function table(headers, rows, widths) {
  const bd = { style: BorderStyle.SINGLE, size: 4, color: 'BFC7CE' }, borders = { top: bd, bottom: bd, left: bd, right: bd };
  const cell = (x, head, w) => new TableCell({ width: { size: w, type: WidthType.DXA }, borders,
    shading: head ? { fill: 'DCE6EC', type: ShadingType.CLEAR, color: 'auto' } : undefined, margins: { top: 50, bottom: 50, left: 90, right: 90 },
    children: [new Paragraph({ children: [t(String(x), { bold: head, size: 19 })] })] });
  return new Table({ width: { size: widths.reduce((a, b) => a + b), type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: headers.map((x, i) => cell(x, true, widths[i])) }), ...rows.map(r => new TableRow({ children: r.map((x, i) => cell(x, false, widths[i])) }))] });
}
const body = [];
function calc(num, title, o) {
  body.push(H1(`C${num}  ${title}`));
  if (o.fbd) body.push(...img(path.join(ROOT, `calcs/${o.fbd}.png`), 6.3, o.fbdCap));
  if (o.given) { body.push(label('Given')); o.given.forEach(x => body.push(bullet(x))); }
  if (o.find) { body.push(label('Find')); o.find.forEach(x => body.push(bullet(x))); }
  if (o.assume) { body.push(label('Assumptions')); o.assume.forEach(x => body.push(bullet(x))); }
  if (o.eqs) { body.push(label('Equations')); o.eqs.forEach(x => body.push(EQ(x))); }
  if (o.sol) { body.push(label('Solution')); o.sol.forEach(x => body.push(typeof x === 'string' ? EQ(x) : x)); }
  if (o.res) { body.push(label('')); body.push(result(o.res)); }
  if (o.note) body.push(P([t('Note: ', { bold: true, italics: true }), t(o.note, { italics: true })], { spacing: { before: 120, after: 120 } }));
}

const c = D.cycle, s1 = D.stage1, s2 = D.stage2, pw = D.power, r = D.rotor, th = D.thrust, sr = D.stress, cr = D.critical, cf = D.cfd, df = D.diffuser, pp = D.pipes;

// ---- title
body.push(
  new Paragraph({ spacing: { before: 2000, after: 200 }, alignment: AlignmentType.CENTER, children: [t('Hand-Calculation Package', { bold: true, size: 44 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 300 }, children: [t('Two-stage magnetic-bearing centrifugal compressor (Turbocor TTS350 class, R-513A)', { size: 26, color: '444444' })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 1000 }, children: [t('Free-body diagrams, control volumes and every sizing calculation behind the design', { italics: true, size: 22 })] }),
  P('How to use this package: each calculation follows the same pattern used in engineering calc books: Given, Find, Assumptions, Equations, Solution, Result. Values come from the design scripts in this repository (meanline.py and hand_calcs.py), so every number can be reproduced with a calculator and a refrigerant property table. Properties are real-gas R-513A from CoolProp (a 56/44 % by mass R-1234yf/R-134a mixture), except calculation C19, which uses R-134a to match the CFD material.'),
  P([t('Calculations C14–C18 (bearing loads, unbalance, axial thrust, disc stress, critical speed) are first-order estimates made for this package. They use simplified models and are labelled as such. Use them to check orders of magnitude, not as final design values.', { italics: true })]),
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [t('Contents')] }),
  new TableOfContents('Contents', { hyperlink: true, headingStyleRange: '1-1' }),
  P([t('Right-click and choose Update Field in Word to fill in the page numbers.', { italics: true, size: 18, color: '777777' })]),
  new Paragraph({ children: [new PageBreak()] }),
);

calc(1, 'Design requirements and refrigerant state points', {
  fbd: 'FBD-1_cycle', fbdCap: 'FBD-1. Chiller cycle with the four state points and the compressor control volume.',
  given: [`Capacity Q̇_evap = ${c.tons} tons × 3.51685 kW/ton = ${f(c.Q_evap_kW, 1)} kW (TCAA220, two compressors)`,
          `Saturated suction ${f(c.Te_C, 1)} °C, saturated discharge ${f(c.Tc_C, 1)} °C (AHRI air-cooled rating)`, 'Superheat 3 K at compressor inlet, subcooling 5 K leaving the condenser', 'Refrigerant R-513A'],
  find: ['Evaporator and condenser pressures, inlet state (1), liquid enthalpy (3 = 4)'],
  assume: ['Steady state; no pressure drop in heat exchangers or piping', 'Throttling at the expansion valve is isenthalpic (h₄ = h₃)'],
  eqs: ['P_evap = P_sat(T_evap),   P_cond = P_sat(T_cond)', 'State 1: (P_evap, T_evap + 3 K) → h₁, s₁, ρ₁, a₁', 'State 3: (P_cond, T_cond − 5 K) → h₃ = h₄'],
  sol: [`P_evap = P_sat(${f(c.Te_C, 1)} °C) = ${f(c.P_ev_kPa, 1)} kPa`, `P_cond = P_sat(${f(c.Tc_C, 1)} °C) = ${f(c.P_cd_kPa, 1)} kPa`,
        `State 1: T₁ = ${f(c.T1_C, 1)} °C → h₁ = ${f(c.h1, 2)} kJ/kg, s₁ = ${f(c.s1, 4)} kJ/kg·K, ρ₁ = ${f(c.rho1, 2)} kg/m³, a₁ = ${f(c.a1, 1)} m/s`,
        `State 3: T₃ = ${f(c.Tc_C - 5, 1)} °C → h₃ = h₄ = ${f(c.h4, 2)} kJ/kg`],
  res: [`P_evap = ${f(c.P_ev_kPa, 0)} kPa,  P_cond = ${f(c.P_cd_kPa, 0)} kPa,  h₁ = ${f(c.h1, 1)} kJ/kg,  h₄ = ${f(c.h4, 1)} kJ/kg`],
});
calc(2, 'Mass flow and suction volume flow', {
  given: [`Q̇_evap = ${f(c.Q_evap_kW, 1)} kW, h₁ = ${f(c.h1, 2)} kJ/kg, h₄ = ${f(c.h4, 2)} kJ/kg, ρ₁ = ${f(c.rho1, 2)} kg/m³`],
  find: ['Refrigerant mass flow ṁ and suction volume flow V̇'],
  assume: ['Evaporator control volume: steady, no work, negligible kinetic/potential energy changes'],
  eqs: ['Q̇_evap = ṁ (h₁ − h₄)', 'V̇ = ṁ / ρ₁'],
  sol: [`q_evap = h₁ − h₄ = ${f(c.h1, 2)} − ${f(c.h4, 2)} = ${f(c.q_evap, 2)} kJ/kg`, `ṁ = ${f(c.Q_evap_kW, 1)} / ${f(c.q_evap, 2)} = ${f(c.mdot, 3)} kg/s`, `V̇ = ${f(c.mdot, 3)} / ${f(c.rho1, 2)} = ${f(c.Vdot, 4)} m³/s`],
  res: [`ṁ = ${f(c.mdot, 3)} kg/s,  V̇ = ${f(c.Vdot, 3)} m³/s`],
});
calc(3, 'Pressure ratio, ideal work and stage split', {
  fbd: 'FBD-2_compressor_CV', fbdCap: 'FBD-2. Compressor control volume for the steady-flow energy equation.',
  given: [`P_evap = ${f(c.P_ev_kPa, 1)} kPa, P_cond = ${f(c.P_cd_kPa, 1)} kPa, s₁ = ${f(c.s1, 4)} kJ/kg·K`],
  find: ['Overall and per-stage pressure ratio; isentropic work'],
  assume: ['Two stages with equal pressure ratio (first guess); adiabatic compressor'],
  eqs: ['PR = P_cond / P_evap,   PR_stage ≈ √PR', 'Δh₀s = h(P_cond, s₁) − h₁', 'Ẇ = ṁ (h₀₂ − h₀₁)'],
  sol: [`PR = ${f(c.P_cd_kPa, 1)} / ${f(c.P_ev_kPa, 1)} = ${f(c.PR, 3)}`, `PR_stage ≈ √${f(c.PR, 3)} = ${f(c.PR_stage, 3)}`,
        `h₂s = h(${f(c.P_cd_kPa, 0)} kPa, s₁) = ${f(c.h2s, 2)} kJ/kg → Δh₀s = ${f(c.dhs_total, 2)} kJ/kg`,
        `With η_stage = ${s1.eta_stage}, stage-1 work ≈ Δh₀s,1/η = ${f(s1.dhs, 2)} / ${s1.eta_stage} = ${f(s1.dhs / s1.eta_stage, 2)} kJ/kg (iterated: ${f(s1.dh0, 2)} kJ/kg)`],
  res: [`PR = ${f(c.PR, 2)} overall, ≈ ${f(c.PR_stage, 2)} per stage;  Δh₀s,total = ${f(c.dhs_total, 1)} kJ/kg`],
});
calc(4, 'Slip factor and work coefficient', {
  fbd: 'FBD-3_euler_CV', fbdCap: 'FBD-3. Impeller control volume for angular momentum (Euler equation).',
  given: [`Z = ${s1.Z} blades (7 main + 7 splitter), exit blade angle β₂b = ${s1.beta2b}° (backswept, from radial), φ₂ = Cm₂/U₂ = ${s1.phi2}`],
  find: ['Slip factor σ and work coefficient ψ = Δh₀/U₂²'],
  assume: ['No inlet swirl (IGVs open): Cθ₁ = 0', 'Wiesner slip correlation; splitters counted as full blades'],
  eqs: ['σ = 1 − √(cos β₂b) / Z^0.7   (Wiesner)', 'Cθ₂ = σ U₂ − Cm₂ tan β₂b', 'Δh₀ = U₂ Cθ₂ → ψ = σ − φ₂ tan β₂b'],
  sol: [`σ = 1 − √(cos 40°) / 14^0.7 = 1 − ${f(Math.sqrt(Math.cos(40 * Math.PI / 180)), 4)} / ${f(Math.pow(14, 0.7), 3)} = ${f(s1.sigma, 3)}`,
        `(for comparison, 7 blades only: σ = ${f(s1.sigma7, 3)})`, `ψ = ${f(s1.sigma, 3)} − ${s1.phi2} × tan 40° = ${f(s1.sigma, 3)} − ${f(s1.phi2 * Math.tan(40 * Math.PI / 180), 3)} = ${f(s1.psi, 3)}`],
  res: [`σ = ${f(s1.sigma, 3)},  ψ = ${f(s1.psi, 3)}`],
});
calc(5, 'Stage-1 tip speed and tip diameter', {
  given: [`Required Δh₀ = ${f(s1.dh0, 2)} kJ/kg (from C3, iterated), ψ = ${f(s1.psi, 3)}, N = ${s1.N.toLocaleString()} rpm`],
  find: ['Tip speed U₂ and diameter D₂'],
  assume: ['Both stages use the same D₂ (one shaft, one speed); D₂ iterated until two stages reach P_cond'],
  eqs: ['U₂ = √(Δh₀ / ψ)', 'D₂ = 60 U₂ / (π N)', 'ω = 2πN/60'],
  sol: [`U₂ = √(${f(s1.dh0 * 1000, 0)} / ${f(s1.psi, 3)}) = ${f(s1.U2, 1)} m/s`, `ω = 2π × ${s1.N} / 60 = ${f(s1.omega, 1)} rad/s`, `D₂ = 60 × ${f(s1.U2, 1)} / (π × ${s1.N}) = ${f(s1.D2_mm / 1000, 4)} m`],
  res: [`U₂ = ${f(s1.U2, 1)} m/s,  D₂ = ${f(s1.D2_mm, 1)} mm (r₂ = ${f(s1.r2_mm, 2)} mm)`],
  note: 'Check: the tip Mach number U₂/a₁ ≈ 1.15 is typical for refrigerant compressors because refrigerants have low speeds of sound.',
});
calc(6, 'Inlet eye sizing', {
  fbd: 'FBD-4_velocity_triangles', fbdCap: 'FBD-4. Velocity triangles at the stage-1 inlet tip and exit, to scale.',
  given: [`ṁ = ${f(c.mdot, 3)} kg/s, hub/tip ratio D₁h/D₁t = ${s1.hub_ratio}, ω = ${f(s1.omega, 1)} rad/s, inlet total state from C1`],
  find: ['Eye tip diameter D₁t that minimises the relative Mach number at the blade tip'],
  assume: ['Uniform axial inflow, no swirl; static density from isentropic acceleration (iterated)'],
  eqs: ['A₁ = π/4 (D₁t² − D₁h²),   Cm₁ = ṁ / (ρ₁ A₁)', 'U₁t = ω D₁t / 2,   W₁t = √(Cm₁² + U₁t²)', 'M₁rel = W₁t / a₁,   β₁t = atan(U₁t / Cm₁)'],
  sol: ['Small D₁t → high Cm₁; large D₁t → high U₁t. Scanning D₁t gives a minimum W₁t at:',
        `D₁t = ${f(s1.D1t_mm, 1)} mm, D₁h = ${f(s1.D1h_mm, 1)} mm → A₁ = ${f(s1.A1_mm2, 0)} mm²`,
        `ρ₁,static = ${f(s1.rho1, 2)} kg/m³ → Cm₁ = ${f(s1.Cm1, 1)} m/s`, `U₁t = ${f(s1.omega, 1)} × ${f(s1.D1t_mm / 2000, 4)} = ${f(s1.U1t, 1)} m/s`,
        `W₁t = √(${f(s1.Cm1, 1)}² + ${f(s1.U1t, 1)}²) = ${f(s1.W1t, 1)} m/s → M₁rel = ${f(s1.M1rel, 3)},  β₁t = ${f(s1.beta1t, 1)}°`],
  res: [`D₁t = ${f(s1.D1t_mm, 1)} mm,  M₁rel = ${f(s1.M1rel, 2)} (below 0.9, so no strong shock),  blade inlet angle β₁t = ${f(s1.beta1t, 1)}° + 2° incidence`],
});
calc(7, 'Impeller exit width and exit velocities', {
  given: [`U₂ = ${f(s1.U2, 1)} m/s, φ₂ = ${s1.phi2}, σ = ${f(s1.sigma, 3)}, β₂b = 40°, exit static density ρ₂ = ${f(s1.rho2, 2)} kg/m³, blockage B = ${s1.blockage}`],
  find: ['Exit width b₂, exit velocities, absolute flow angle α₂ and Mach number'],
  assume: ['Impeller total-to-total efficiency 0.90 to fix the exit state'],
  eqs: ['Cm₂ = φ₂ U₂,   Cθ₂ = σU₂ − Cm₂ tan β₂b,   C₂ = √(Cm₂² + Cθ₂²)', 'b₂ = ṁ / [ρ₂ π D₂ Cm₂ (1 − B)]', 'α₂ = atan(Cθ₂ / Cm₂)'],
  sol: [`Cm₂ = ${s1.phi2} × ${f(s1.U2, 1)} = ${f(s1.Cm2, 2)} m/s`, `Cθ₂ = ${f(s1.sigma, 3)} × ${f(s1.U2, 1)} − ${f(s1.Cm2, 2)} × tan 40° = ${f(s1.Ct2, 2)} m/s`,
        `C₂ = ${f(s1.C2, 1)} m/s,  α₂ = ${f(s1.alpha2, 1)}°,  M₂ = ${f(s1.M2, 3)}`,
        `b₂ = ${f(c.mdot, 3)} / (${f(s1.rho2, 2)} × π × ${f(s1.D2_mm / 1000, 4)} × ${f(s1.Cm2, 2)} × ${1 - s1.blockage}) = ${f(s1.b2_mm / 1000, 5)} m`],
  res: [`b₂ = ${f(s1.b2_mm, 2)} mm,  Cθ₂ = ${f(s1.Ct2, 1)} m/s,  α₂ = ${f(s1.alpha2, 1)}°,  stage-1 PR = ${f(s1.PR, 3)}`],
});
body.push(H1('C8  Stage 2 (same method as C4–C7)'));
body.push(table(['Quantity', 'Stage 1', 'Stage 2'], [
  ['Inlet total pressure / temperature', `${f(c.P_ev_kPa, 0)} kPa / ${f(c.T1_C, 1)} °C`, `${f(s2.P_in_kPa, 0)} kPa / ${f(s2.T_in_C, 1)} °C`],
  ['Tip diameter / tip speed', `${f(s1.D2_mm, 1)} mm / ${f(s1.U2, 1)} m/s`, `${f(s2.D2 * 1000, 1)} mm / ${f(s2.U2, 1)} m/s`],
  ['Eye tip / hub diameter', `${f(s1.D1t_mm, 1)} / ${f(s1.D1h_mm, 1)} mm`, `${f(s2.D1t * 1000, 1)} / ${f(s2.D1h * 1000, 1)} mm`],
  ['Cm₁ / W₁t / M₁rel', `${f(s1.Cm1, 1)} / ${f(s1.W1t, 1)} / ${f(s1.M1rel, 2)}`, `${f(s2.Cm1, 1)} / ${f(s2.W1t, 1)} / ${f(s2.M1rel, 2)}`],
  ['Exit width b₂', `${f(s1.b2_mm, 2)} mm`, `${f(s2.b2 * 1000, 2)} mm`],
  ['Exit density ρ₂', `${f(s1.rho2, 1)} kg/m³`, `${f(s2.rho2, 1)} kg/m³`],
  ['Work Δh₀', `${f(s1.dh0, 2)} kJ/kg`, `${f(s2.work_kJkg, 2)} kJ/kg`],
  ['Stage pressure ratio', f(s1.PR, 3), f(s2.PR, 3)],
  ['Outlet total pressure / temperature', `${f(s1.P_out_kPa, 0)} kPa / ${f(s1.T_out_C, 1)} °C`, `${f(s2.P_out_kPa, 0)} kPa / ${f(s2.T_out_C, 1)} °C`],
], [3360, 3000, 3000]));
body.push(P(''), P('Stage 2 handles the same mass flow at about twice the density, so its eye is smaller and its exit width is about half that of stage 1.'));
calc(9, 'Vaneless diffuser and de-swirl vane inlet angle', {
  given: [`r₂ = ${f(df.r2_mm, 2)} mm, r₃ = ${f(df.r3_mm, 1)} mm (r₃/r₂ = 1.55), b₃ = ${f(df.b3_mm, 2)} mm, Cθ₂ = ${f(s1.Ct2, 1)} m/s, Cm₂ = ${f(s1.Cm2, 1)} m/s`],
  find: ['Velocities at the diffuser exit; inlet metal angle of the de-swirl (return-channel) vanes'],
  assume: ['Free vortex in the vaneless space (no wall friction): r Cθ = constant', 'Density nearly constant across the diffuser (first estimate)'],
  eqs: ['Cθ₃ = Cθ₂ r₂ / r₃', 'Cm₃ = Cm₂ (r₂ b₂) / (r₃ b₃)   (continuity)', 'α₃ = atan(Cθ₃ / Cm₃)'],
  sol: [`Cθ₃ = ${f(s1.Ct2, 1)} × ${f(df.r2_mm, 1)} / ${f(df.r3_mm, 1)} = ${f(df.Ct3, 1)} m/s`, `Cm₃ = ${f(s1.Cm2, 1)} × (${f(df.r2_mm, 1)} × ${f(s1.b2_mm, 2)}) / (${f(df.r3_mm, 1)} × ${f(df.b3_mm, 2)}) = ${f(df.Cm3, 1)} m/s`,
        `C₃ = ${f(df.C3, 1)} m/s (down from ${f(s1.C2, 1)} m/s → static pressure recovery)`, `De-swirl vane inlet angle (with density correction) = ${f(df.deswirl_in, 1)}° from radial`],
  res: [`C₃ ≈ ${f(df.C3, 0)} m/s;  de-swirl vanes: inlet ${f(df.deswirl_in, 1)}°, exit 0° (radial, no swirl into stage 2)`],
});
const vs = D.volute.sections;
calc(10, 'Volute cross-sections', {
  given: [`Volume flow at the volute Q = ${f(D.volute.Q_m3s * 1000, 1)} L/s, stage-2 exit angular momentum K = Cθ₂ r₂ = ${f(D.volute.K, 3)} m²/s, r₃ = ${f(df.r3_mm, 1)} mm`],
  find: ['Circular section diameter d(θ) around the volute'],
  assume: ['Constant angular momentum (free vortex) inside the volute', 'Circular, external sections tangent to the diffuser exit (+2 mm lip)'],
  eqs: ['Flow through section θ: Q θ/(2π) = ∫ Cθ dA ≈ K · A / R_c', 'A(θ) = Q θ R_c / (2π K),   R_c = r₃ + d/2 + 2 mm,   d = √(4A/π)  (iterate)'],
  sol: [new Paragraph({ children: [] })],
  res: [`d grows from 0 at the tongue to ${f(vs[vs.length - 1].d, 1)} mm at 360° (R_c = ${f(vs[vs.length - 1].rc, 1)} mm)`],
});
body.splice(body.length - 1, 0, table(['θ (deg)', 'd (mm)', 'R_c (mm)', 'Area (mm²)'], vs.map(v => [f(v.theta, 0), f(v.d, 1), f(v.rc, 1), f(Math.PI * v.d * v.d / 4, 0)]), [2340, 2340, 2340, 2340]));
calc(11, 'Suction and discharge pipe sizing', {
  given: [`V̇_suction = ${f(c.Vdot, 4)} m³/s; discharge density ρ = ${f(pp.rho_d, 1)} kg/m³ at ${f(c.P_cd_kPa, 0)} kPa, ${f(DP.cycle.T_discharge_C, 0)} °C`],
  find: ['Gas velocity in the DN100 suction and DN50 discharge connections'],
  assume: ['Target vapour-line velocity about 10–25 m/s (low pressure drop and noise)'],
  eqs: ['V = V̇ / (π D² / 4)'],
  sol: [`Suction: V = ${f(c.Vdot, 4)} / (π × ${f(pp.ID_s / 1000, 3)}² / 4) = ${f(pp.V_s, 1)} m/s`, `Discharge: V̇ = ${f(c.mdot, 3)} / ${f(pp.rho_d, 1)} = ${f(pp.Q_d, 4)} m³/s → V = ${f(pp.V_d, 1)} m/s in Ø${pp.ID_d} mm`],
  res: [`Suction DN100: ${f(pp.V_s, 1)} m/s;  discharge DN50: ${f(pp.V_d, 1)} m/s (both within the target range)`],
});
calc(12, 'Power, torque, efficiency and kW/ton', {
  given: [`ṁ = ${f(c.mdot, 3)} kg/s, Δh₀ = ${f(s1.dh0, 2)} + ${f(s2.work_kJkg, 2)} kJ/kg, mechanical loss 2 %, motor × drive efficiency 0.95, ω = ${f(s1.omega, 1)} rad/s`],
  find: ['Gas, shaft and electrical power; torque; overall efficiency; kW/ton and COP'],
  eqs: ['Ẇ_gas = ṁ Σ Δh₀,   Ẇ_shaft = Ẇ_gas (1 + 0.02),   Ẇ_in = Ẇ_shaft / 0.95', 'T = Ẇ_shaft / ω', 'η_s = Δh₀s / Σ Δh₀,   kW/ton = Ẇ_in / tons,   COP = Q̇_evap / Ẇ_in'],
  sol: [`Ẇ_gas = ${f(c.mdot, 3)} × ${f(pw.dh_total, 2)} = ${f(pw.P_gas, 1)} kW`, `Ẇ_shaft = ${f(pw.P_shaft, 1)} kW,  Ẇ_in = ${f(pw.P_in, 1)} kW`,
        `T = ${f(pw.P_shaft * 1000, 0)} / ${f(s1.omega, 1)} = ${f(pw.torque, 2)} N·m`, `η_s = ${f(c.dhs_total, 2)} / ${f(pw.dh_total, 2)} = ${f(pw.eta_overall, 3)}`,
        `kW/ton = ${f(pw.P_in, 1)} / ${c.tons} = ${f(pw.kW_ton, 3)},  COP = ${f(c.Q_evap_kW, 1)} / ${f(pw.P_in, 1)} = ${f(pw.COP, 2)}`],
  res: [`Shaft ${f(pw.P_shaft, 0)} kW, input ${f(pw.P_in, 0)} kW, torque ${f(pw.torque, 1)} N·m, ${f(pw.kW_ton, 2)} kW/ton (compressor only)`],
});
calc(13, 'Motor: electrical frequency and rotor shear stress', {
  given: [`N = ${s1.N.toLocaleString()} rpm, 2-pole PM motor, T = ${f(pw.torque, 1)} N·m, rotor Ø70 mm × 170 mm active length`],
  find: ['Inverter output frequency; air-gap shear stress; rotor surface speed'],
  eqs: ['f = N p / 120   (p = number of poles)', 'τ = T / (2π r² L)', 'v = ω r'],
  sol: [`f = ${s1.N} × 2 / 120 = ${f(pw.f_elec, 0)} Hz (mains supply is 60 Hz → 3,600 rpm without the drive)`, `τ = ${f(pw.torque, 1)} / (2π × 0.035² × 0.170) = ${f(pw.shear_kPa, 1)} kPa`, `v = ${f(s1.omega, 1)} × 0.035 = ${f(pw.rotor_tip, 0)} m/s`],
  res: [`${f(pw.f_elec, 0)} Hz;  τ ≈ ${f(pw.shear_kPa, 0)} kPa (typical 20–40 kPa for liquid-cooled high-speed PM motors);  ${f(pw.rotor_tip, 0)} m/s surface speed → carbon-fibre retaining sleeve`],
});
calc(14, 'Rotor mass, centre of gravity and radial bearing reactions (estimate)', {
  fbd: 'FBD-6_rotor_radial', fbdCap: 'FBD-6. Rotor radial free-body diagram.',
  given: ['Rotor segment table (drawing TC-103); steel ρ = 7800 kg/m³; aluminium impellers ρ = 2810 kg/m³', `Radial bearing centres x_A = ${f(r.xA, 0)} mm, x_B = ${f(r.xB, 0)} mm`],
  find: ['Rotor mass, CG location, static bearing reactions'],
  assume: ['Shaft segments are solid steel cylinders; impeller mass from a simplified solid of revolution', 'Horizontal rotor; gravity only (static)'],
  eqs: ['m = Σ mᵢ,   x_CG = Σ mᵢxᵢ / Σ mᵢ', 'ΣF_y = 0:  R_A + R_B = m g', 'ΣM_A = 0:  R_B (x_B − x_A) = m g (x_CG − x_A)'],
  sol: [`m = ${f(r.m, 2)} kg (PM motor section alone ≈ ${f(r.parts.find(p => p.name.startsWith('PM')).m, 2)} kg),  x_CG = ${f(r.x_cg, 0)} mm`,
        `W = ${f(r.m, 2)} × 9.81 = ${f(r.W, 1)} N`, `R_B = ${f(r.W, 1)} × (${f(r.x_cg, 0)} − ${f(r.xA, 0)}) / ${f(r.span, 0)} = ${f(r.RB, 1)} N`, `R_A = ${f(r.W, 1)} − ${f(r.RB, 1)} = ${f(r.RA, 1)} N`],
  res: [`m ≈ ${f(r.m, 1)} kg;  R_A ≈ ${f(r.RA, 0)} N,  R_B ≈ ${f(r.RB, 0)} N (static)`],
});
body.splice(body.length - 1, 0, table(['Segment', 'Mass (kg)', 'x (mm)'], r.parts.map(p => [p.name, f(p.m, 3), f(p.x, 0)]), [5160, 2100, 2100]), P(''));
calc(15, 'Unbalance force at design speed (estimate)', {
  given: [`Rotor mass m = ${f(r.m, 2)} kg, ω = ${f(s1.omega, 1)} rad/s, balance grade G2.5 (ISO 1940, typical for turbomachinery rotors)`],
  find: ['Residual unbalance eccentricity and rotating force'],
  eqs: ['e = G / ω   (G in m/s)', 'F = m e ω²'],
  sol: [`e = 0.0025 / ${f(s1.omega, 1)} = ${f(r.e_um, 2)} μm`, `F = ${f(r.m, 2)} × ${f(r.e_um * 1e-6, 9)} × ${f(s1.omega, 1)}² = ${f(r.F_unb, 0)} N`],
  res: [`F_unbalance ≈ ${f(r.F_unb, 0)} N rotating at 1× speed, comparable to the rotor weight, so the magnetic bearings are sized for both`],
});
calc(16, 'Axial thrust on the impellers (simplified estimate)', {
  fbd: 'FBD-7_axial_thrust', fbdCap: 'FBD-7. Axial free-body diagram of the two impellers and the thrust disk.',
  given: [`Static pressures from the meanline: stage 1 eye ${f(th.p_eye1, 0)} kPa, exit ${f(th.p_ex1, 0)} kPa; stage 2 eye ${f(th.p_eye2, 0)} kPa, exit ${f(th.p_ex2, 0)} kPa`, `Face area π(r₂² − r_s²) with r_s = ${th.r_s * 1000} mm → ${f(th.s1.A * 1e4, 1)} cm²`],
  find: ['Net axial force the axial magnetic bearing must react'],
  assume: ['Back face sees impeller exit static pressure (no balance holes or seals)', 'Open (blade) side sees the average of eye and exit pressure', 'Inlet axial momentum ṁCm₁ ≈ ρCm₁²A₁ pushes the impeller toward the motor'],
  eqs: ['F_back = p₂ A,   F_front = ½(p_eye + p₂) A,   F_mom = ρ Cm₁² A₁', 'F_net,i = F_back − F_front − F_mom   (positive = toward suction)', 'ΣF_x = 0:  F_axial bearing = Σ F_net,i'],
  sol: [`Stage 1: ${f(th.s1.F_back, 0)} − ${f(th.s1.F_front, 0)} − ${f(th.s1.F_mom, 0)} = ${f(th.s1.F_net, 0)} N`, `Stage 2: ${f(th.s2.F_back, 0)} − ${f(th.s2.F_front, 0)} − ${f(th.s2.F_mom, 0)} = ${f(th.s2.F_net, 0)} N`],
  res: [`F_axial ≈ ${f(th.total / 1000, 2)} kN toward the suction end (upper bound; seals and balance cavities reduce it in practice)`],
});
calc(17, 'Impeller disc stress at overspeed (estimate)', {
  fbd: 'FBD-8_disc_stress', fbdCap: 'FBD-8. Differential element of a rotating disc.',
  given: [`7075-T6: ρ = ${sr.rho} kg/m³, ν = ${sr.nu}, S_y = ${sr.Sy} MPa; r₂ = 51.7 mm, bore r_b = ${sr.rb_mm} mm`],
  find: ['Peak hoop stress at 100 %, 115 % (overspeed test) and maximum speed; safety factor'],
  assume: ['Flat disc of uniform thickness, plane stress; blades ignored (they add load, so FEA is needed to confirm)'],
  eqs: ['d(r σ_r)/dr − σ_θ + ρω²r² = 0', 'σ_θ,max = (3 + ν)/4 · ρω² [r₂² + (1 − ν)/(3 + ν) r_b²]   (at the bore)'],
  sol: [`30,000 rpm: σ_θ = ${f(sr.s_design, 1)} MPa`, `34,500 rpm (115 %): σ_θ = ${f(sr.s_115, 1)} MPa → SF = ${sr.Sy} / ${f(sr.s_115, 1)} = ${f(sr.SF, 1)}`, `39,000 rpm: σ_θ = ${f(sr.s_max, 1)} MPa`],
  res: [`SF ≈ ${f(sr.SF, 1)} at 115 % overspeed for the disc alone`],
});
calc(18, 'First bending critical speed (estimate)', {
  given: [`Steel shaft E = ${cr.E} GPa, ρ = 7800 kg/m³, Ø${cr.d} mm between bearings, span L = ${f(cr.L, 0)} mm`],
  find: ['First bending natural frequency; margin over the 39,000 rpm maximum speed'],
  assume: ['Uniform simply supported beam (rigid supports); overhung impellers and the motor sleeve ignored, which makes this optimistic'],
  eqs: ['ω₁ = (π / L)² √(E I / (ρ A)),   I = πd⁴/64,   A = πd²/4'],
  sol: [`I = ${cr.I.toExponential(3)} m⁴,  A = ${cr.A.toExponential(3)} m²`, `ω₁ = (π / ${f(cr.L / 1000, 3)})² × √(${cr.E}e9 × ${cr.I.toExponential(3)} / (7800 × ${cr.A.toExponential(3)})) = ${f(cr.w1, 0)} rad/s`, `N₁ = ${f(cr.rpm1, 0)} rpm → margin = ${f(cr.margin, 2)} × 39,000 rpm`],
  res: [`First bending critical ≈ ${f(cr.rpm1 / 1000, 0)}k rpm (needs > 1.2 × 39k = 47k rpm). Confirm with a rotordynamics/modal FEA including the impeller and magnet masses.`],
});
calc(19, 'CFD post-processing calculations (stage-1 run, off-design)', {
  fbd: 'FBD-5_rotating_particle', fbdCap: 'FBD-5. Forces on a fluid particle in the rotating frame, the formulation CFX solves.',
  given: [`Mass-averaged totals: P₀,in = ${f(cf.inputs.p1 / 1000, 1)} kPa, P₀,out = ${f(cf.inputs.p2 / 1000, 1)} kPa, T₀,in = ${cf.inputs.T1} K, T₀,out = ${cf.inputs.T2} K (R-134a)`,
          `Per passage: ṁ = ${cf.inputs.m} kg/s, blade torque ${cf.inputs.tq} N·m;  at r = 52 mm: Cθ = ${cf.inputs.Ct52} m/s, Cr = ${cf.inputs.Cr52} m/s`],
  find: ['Pressure ratio, efficiency, specific work three ways, slip factor and exit flow angle'],
  assume: ['Free vortex and continuity to move the r = 52 mm values to r₂ = 51.69 mm'],
  eqs: ['PR = P₀,out/P₀,in;  Δh₀ = h(P₀,out, T₀,out) − h(P₀,in, T₀,in);  η = [h(P₀,out, s_in) − h_in] / Δh₀', 'Δh₀,torque = T ω / ṁ;   Δh₀,Euler = U₂ Cθ₂', 'σ = (Cθ₂ + Cr₂ tan β₂b) / U₂;   α₂ = atan(Cθ₂/Cr₂)'],
  sol: [`PR = ${f(cf.inputs.p2 / 1000, 1)} / ${f(cf.inputs.p1 / 1000, 1)} = ${f(cf.PR, 3)}`, `Δh₀,T = ${f(cf.dh_T, 2)} kJ/kg;  Δh₀s = ${f(cf.dh_s, 2)} kJ/kg → η = ${f(cf.eta, 3)}`,
        `Δh₀,torque = ${cf.inputs.tq} × ${f(s1.omega, 1)} / ${cf.inputs.m} = ${f(cf.dh_tq, 2)} kJ/kg`, `Cθ₂ = ${cf.inputs.Ct52} × 52.0/51.69 = ${f(cf.Ct2, 2)} m/s → Δh₀,Euler = ${f(s1.U2, 1)} × ${f(cf.Ct2, 2)} = ${f(cf.dh_eu, 2)} kJ/kg`,
        `σ = (${f(cf.Ct2, 2)} + ${f(cf.Cr2, 2)} × tan 40°) / ${f(s1.U2, 1)} = ${f(cf.sigma, 3)};  α₂ = ${f(cf.alpha2, 1)}°`, `Stage power = 7 × ${cf.inputs.tq} × ${f(s1.omega, 1)} = ${f(cf.P_total, 1)} kW at ${f(cf.mdot_total, 2)} kg/s`],
  res: [`PR = ${f(cf.PR, 3)}, η = ${f(cf.eta, 2)};  work: ${f(cf.dh_T, 1)} / ${f(cf.dh_tq, 1)} / ${f(cf.dh_eu, 1)} kJ/kg (temperature / torque / Euler, within 3 %);  σ = ${f(cf.sigma, 2)}, α₂ = ${f(cf.alpha2, 1)}°`],
});

body.push(H1('Symbols'));
body.push(table(['Symbol', 'Meaning', 'Units'], [
  ['ṁ', 'mass flow rate', 'kg/s'], ['h, h₀', 'static, total enthalpy', 'kJ/kg'], ['s', 'entropy', 'kJ/kg·K'], ['P, P₀', 'static, total pressure', 'kPa'],
  ['U', 'blade speed ωr', 'm/s'], ['C, W', 'absolute, relative velocity', 'm/s'], ['Cm, Cr, Cθ', 'meridional, radial, swirl (tangential) velocity', 'm/s'],
  ['β, α', 'relative, absolute flow angle', 'deg'], ['σ', 'slip factor', '—'], ['φ, ψ', 'flow and work coefficients', '—'], ['M', 'Mach number', '—'],
  ['ω, N', 'angular speed', 'rad/s, rpm'], ['T', 'torque', 'N·m'], ['σ_r, σ_θ', 'radial, hoop stress', 'MPa'], ['Subscripts', '1 inlet/eye, 2 impeller exit, 3 diffuser exit, t tip, h hub, s isentropic', ''],
], [1800, 5760, 1800]));

const doc = new Document({
  styles: { default: { document: { run: { font: 'Calibri', size: 22 } } },
    paragraphStyles: [{ id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
      run: { size: 28, bold: true, font: 'Calibri', color: '1F3A4D' }, paragraph: { spacing: { before: 360, after: 140 }, outlineLevel: 0 } }] },
  numbering: { config: [{ reference: 'b', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: ['Hand-calculation package · page ', PageNumber.CURRENT], size: 18, color: '777777' })] })] }) },
    children: body }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(path.join(ROOT, 'calcs/Hand_Calculation_Package.docx'), b); console.log('ok'); });
