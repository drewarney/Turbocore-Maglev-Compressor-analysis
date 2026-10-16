"""Tiny 2-D drafting toolkit on top of matplotlib: A3 sheets, views, dimensions."""
import math
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle, FancyArrowPatch
import numpy as np

A3 = (420.0, 297.0)
MM = 1 / 25.4
INK = "#111111"
DIM = "#1f4e9e"
CL = "#b03030"
FILLS = dict(cast="#d9dde3", rotor="#f2d27a", copper="#e0a070", steel="#c8ccd2",
             magnet="#9fb7d9", alu="#e6e6e6", fluid="#cfe8f7", elec="#b9d3b0", blade="#f7e6b5")
PROJECT = "Turbocor-class 2-stage maglev centrifugal compressor (R-513A)"


class Sheet:
    def __init__(self, number, title, scale="AS NOTED", sheet=1, of=1, material="", notes=None):
        self.fig = plt.figure(figsize=(A3[0] * MM, A3[1] * MM))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, A3[0])
        self.ax.set_ylim(0, A3[1])
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        a = self.ax
        a.add_patch(Rectangle((10, 10), 400, 277, fill=False, lw=1.2, ec=INK))
        # title block
        x0, y0, w, h = 250, 10, 160, 36
        a.add_patch(Rectangle((x0, y0), w, h, fill=False, lw=1.0, ec=INK))
        for yy in (y0 + 12, y0 + 24):
            a.plot([x0, x0 + w], [yy, yy], lw=0.6, c=INK)
        a.plot([x0 + 110, x0 + 110], [y0, y0 + 24], lw=0.6, c=INK)
        a.text(x0 + 2, y0 + 30, title, fontsize=10, weight="bold", va="center")
        a.text(x0 + 2, y0 + 18, PROJECT, fontsize=5.6, va="center")
        a.text(x0 + 2, y0 + 6, f"DWG {number}    SCALE {scale}    UNITS mm", fontsize=6.5, va="center")
        a.text(x0 + 112, y0 + 18, f"SHEET {sheet} OF {of}", fontsize=6.5, va="center")
        a.text(x0 + 112, y0 + 6, f"REV A  {date.today():%Y-%m-%d}", fontsize=6.5, va="center")
        if material:
            a.add_patch(Rectangle((x0, y0 + h), w, 8, fill=False, lw=0.6, ec=INK))
            a.text(x0 + 2, y0 + h + 4, f"MATERIAL: {material}", fontsize=6, va="center")
        a.text(12, 13, "Reverse-engineered study model - NOT OEM geometry. Third-angle projection. "
               "General tolerance +/-0.5 mm unless noted.", fontsize=5.5, color="#555")
        if notes:
            self.notes(notes)

    def view(self, ox, oy, scale, label=None, label_xy=None):
        """label_xy = paper position of the view title (defaults to just below the origin)."""
        v = View(self.ax, ox, oy, scale)
        if label:
            lx, ly = label_xy or (ox, oy - 8)
            self.ax.text(lx, ly, label, fontsize=7.5, weight="bold", ha="center")
        return v

    def notes(self, lines, x=14, y=60, title="NOTES", size=6.0):
        self.ax.text(x, y, title, fontsize=size + 1, weight="bold", va="top")
        for i, ln in enumerate(lines):
            self.ax.text(x, y - 4.2 - i * 3.6, f"{i + 1}. {ln}" if title == "NOTES" else ln,
                         fontsize=size, va="top")

    def table(self, x, y, rows, widths, title=None, size=5.8, row_h=4.2):
        a = self.ax
        if title:
            a.text(x, y + 2, title, fontsize=size + 1, weight="bold")
        for i, row in enumerate(rows):
            yy = y - i * row_h
            cx = x
            for j, (cell, w) in enumerate(zip(row, widths)):
                a.add_patch(Rectangle((cx, yy - row_h), w, row_h, fill=(i == 0), fc="#eeeeee",
                                      ec=INK, lw=0.4))
                a.text(cx + 1, yy - row_h / 2, str(cell), fontsize=size, va="center",
                       weight="bold" if i == 0 else "normal")
                cx += w

    def text(self, x, y, s, **kw):
        kw.setdefault("fontsize", 6.5)
        self.ax.text(x, y, s, **kw)

    def save(self, pdf, png_path=None):
        pdf.savefig(self.fig)
        if png_path:
            self.fig.savefig(png_path, dpi=110)
        plt.close(self.fig)


class View:
    """Maps model mm to paper mm: paper = origin + scale * model."""

    def __init__(self, ax, ox, oy, s):
        self.ax, self.ox, self.oy, self.s = ax, ox, oy, s

    def P(self, pts):
        pts = np.atleast_2d(np.asarray(pts, float))
        return np.column_stack([self.ox + self.s * pts[:, 0], self.oy + self.s * pts[:, 1]])

    def line(self, pts, lw=0.7, c=INK, ls="-", z=3):
        p = self.P(pts)
        self.ax.plot(p[:, 0], p[:, 1], lw=lw, c=c, ls=ls, zorder=z, solid_capstyle="round")

    def poly(self, pts, fc=None, ec=INK, lw=0.6, hatch=None, z=2, alpha=1.0):
        self.ax.add_patch(Polygon(self.P(pts), closed=True, fc=fc or "none", ec=ec, lw=lw,
                                  hatch=hatch, zorder=z, alpha=alpha))

    def rect(self, x0, y0, x1, y1, **kw):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], **kw)

    def mirror_rect(self, x0, r0, x1, r1, **kw):
        """Axisymmetric part shown in section: draw above and below the axis."""
        self.rect(x0, r0, x1, r1, **kw)
        self.rect(x0, -r0, x1, -r1, **kw)

    def mirror_poly(self, pts, **kw):
        pts = np.asarray(pts, float)
        self.poly(pts, **kw)
        self.poly(pts * [1, -1], **kw)

    def circle(self, c, r, lw=0.7, ec=INK, fc="none", ls="-", z=3):
        (px, py), = self.P([c])
        self.ax.add_patch(Circle((px, py), r * self.s, fc=fc, ec=ec, lw=lw, ls=ls, zorder=z))

    def centerline(self, p0, p1):
        self.line([p0, p1], lw=0.45, c=CL, ls=(0, (8, 2, 1.5, 2)), z=5)

    def center_mark(self, c, r):
        x, y = c
        self.centerline((x - r, y), (x + r, y))
        self.centerline((x, y - r), (x, y + r))

    def text(self, p, s, size=6.0, **kw):
        (px, py), = self.P([p])
        kw.setdefault("ha", "center")
        kw.setdefault("va", "center")
        self.ax.text(px, py, s, fontsize=size, zorder=8, **kw)

    def leader(self, p, q, s, size=5.8):
        """Leader from model point p to model point q with text at q."""
        (px, py), (qx, qy) = self.P([p, q])
        self.ax.annotate(s, xy=(px, py), xytext=(qx, qy), fontsize=size, zorder=9,
                         ha="left" if qx >= px else "right", va="center",
                         arrowprops=dict(arrowstyle="-|>", lw=0.45, color=INK,
                                         shrinkA=0, shrinkB=0, mutation_scale=5))

    def balloon(self, p, q, n):
        (px, py), (qx, qy) = self.P([p, q])
        self.ax.plot([px, qx], [py, qy], lw=0.45, c=INK, zorder=9)
        self.ax.plot([px], [py], "o", ms=1.5, c=INK, zorder=9)
        self.ax.add_patch(Circle((qx, qy), 3.2, fc="white", ec=INK, lw=0.6, zorder=10))
        self.ax.text(qx, qy, str(n), fontsize=5.5, ha="center", va="center", zorder=11)

    def _arrow(self, a, b):
        self.ax.add_patch(FancyArrowPatch(a, b, arrowstyle="<|-|>", mutation_scale=5,
                                          lw=0.45, color=DIM, shrinkA=0, shrinkB=0, zorder=7))

    def dim(self, p0, p1, off, text=None, orient="h", prefix="", fmt="{:.1f}", size=5.6):
        """Linear dimension between model points. orient 'h' (x distance), 'v' (y distance)
        or 'a' (aligned). off = offset of the dimension line in PAPER mm."""
        (x0, y0), (x1, y1) = self.P([p0, p1])
        if orient == "h":
            val = abs(p1[0] - p0[0])
            yd = (max(y0, y1) if off > 0 else min(y0, y1)) + off
            a, b = (x0, yd), (x1, yd)
            ext = [((x0, y0), (x0, yd + math.copysign(1.2, off))), ((x1, y1), (x1, yd + math.copysign(1.2, off)))]
            tp, rot = ((x0 + x1) / 2, yd + math.copysign(1.6, off)), 0
        elif orient == "v":
            val = abs(p1[1] - p0[1])
            xd = (max(x0, x1) if off > 0 else min(x0, x1)) + off
            a, b = (xd, y0), (xd, y1)
            ext = [((x0, y0), (xd + math.copysign(1.2, off), y0)), ((x1, y1), (xd + math.copysign(1.2, off), y1))]
            tp, rot = (xd + math.copysign(1.6, off), (y0 + y1) / 2), 90
        else:
            val = math.dist(p0, p1)
            d = np.array([x1 - x0, y1 - y0]); d /= np.linalg.norm(d)
            n = np.array([-d[1], d[0]]) * off
            a, b = (x0 + n[0], y0 + n[1]), (x1 + n[0], y1 + n[1])
            ext = [((x0, y0), a), ((x1, y1), b)]
            nn = n / (abs(off) or 1) * 1.8
            tp = ((a[0] + b[0]) / 2 + nn[0], (a[1] + b[1]) / 2 + nn[1])
            rot = math.degrees(math.atan2(d[1], d[0]))
            if rot > 90 or rot < -90:
                rot += 180
        for e0, e1 in ext:
            self.ax.plot([e0[0], e1[0]], [e0[1], e1[1]], lw=0.3, c=DIM, zorder=6)
        self._arrow(a, b)
        label = text if text is not None else prefix + fmt.format(val)
        self.ax.text(tp[0], tp[1], label, fontsize=size, color=DIM, ha="center", va="center",
                     rotation=rot, zorder=8,
                     bbox=dict(fc="white", ec="none", pad=0.25, alpha=0.85))

    def dia(self, c, r, ang=45, text=None, size=5.6, out=8):
        """Diameter callout with leader on a circle seen face-on."""
        a = math.radians(ang)
        p = (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
        q = (c[0] + (r + out / self.s) * math.cos(a), c[1] + (r + out / self.s) * math.sin(a))
        (px, py), (qx, qy) = self.P([p, q])
        self.ax.annotate(text or f"Ø{2 * r:.1f}", xy=(px, py), xytext=(qx, qy), fontsize=size,
                         color=DIM, ha="left" if math.cos(a) >= 0 else "right", va="center",
                         zorder=9, arrowprops=dict(arrowstyle="-|>", lw=0.45, color=DIM,
                                                   shrinkA=0, shrinkB=0, mutation_scale=5))
