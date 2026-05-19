"""
systemArchitecture.py
Generates a polished dark-theme architecture diagram for the hybrid
embedded water leak detection and localisation system.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
BG       = "#0d1117"
BG_PANEL = "#161b22"
BORDER   = "#30363d"

C_SENSOR = "#58a6ff"   # blue   – sensors / sources
C_COND   = "#3fb950"   # green  – signal conditioning
C_ADC    = "#e3b341"   # amber  – ADC
C_MCU    = "#f85149"   # red    – MCU / processing
C_FLOW   = "#58a6ff"   # blue   – flow inputs
C_OUT    = "#bc8cff"   # purple – outputs
C_ARROW  = "#8b949e"
C_TITLE  = "#e6edf3"
C_LABEL  = "#8b949e"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
BW = 2.5    # box width
BH = 0.50   # base box height

def box(ax, x, y, w, h, label, fc, fontsize=8.2):
    patch = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.06",
        linewidth=1.0,
        edgecolor=fc,
        facecolor=BG_PANEL,
        zorder=3,
        clip_on=False,
    )
    ax.add_patch(patch)
    # left colour bar
    bar = FancyBboxPatch(
        (x - w / 2, y - h / 2), 0.07, h,
        boxstyle="round,pad=0.0",
        linewidth=0,
        facecolor=fc,
        zorder=4,
        clip_on=False,
    )
    ax.add_patch(bar)
    ax.text(
        x + 0.05, y, label,
        ha="center", va="center",
        fontsize=fontsize, color=C_TITLE,
        fontweight="bold", zorder=5,
        multialignment="center",
        fontfamily="monospace",
    )

def arr(ax, x1, y1, x2, y2):
    ax.annotate(
        "",
        xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>",
            color=C_ARROW,
            lw=1.2,
            mutation_scale=10,
        ),
        zorder=2,
    )

def section_label(ax, x, y, text):
    ax.text(x, y, text,
            ha="center", va="center",
            fontsize=8, color=C_LABEL,
            fontstyle="italic", fontfamily="monospace",
            zorder=5)

def panel(ax, x, y, w, h):
    p = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.1",
        linewidth=1.0,
        edgecolor=BORDER,
        facecolor="#1a2030",
        zorder=1,
        alpha=0.5,
    )
    ax.add_patch(p)

# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(16, 11))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 16)
ax.set_ylim(0, 11)
ax.axis("off")

# Title
ax.text(8, 10.55,
        "Hybrid Embedded Water Leak Detection & Localisation System",
        ha="center", va="center",
        fontsize=13.5, fontweight="bold",
        color=C_TITLE, fontfamily="monospace", zorder=6)
ax.text(8, 10.15,
        "PIC18F2580  ·  Acoustic TDOA  ·  Flow Monitoring",
        ha="center", va="center",
        fontsize=8.5, color=C_LABEL, fontfamily="monospace", zorder=6)

# Thin separator line
ax.plot([0.6, 15.4], [9.85, 9.85], color=BORDER, lw=0.8, zorder=2)

# ===========================================================================
# COLUMN 1 – Flow Subsystem  (x = 2.7)
# ===========================================================================
CX1 = 2.7
panel(ax, CX1 - 1.55, 1.8, 3.1, 7.7)
section_label(ax, CX1, 9.55, "── Flow Monitoring Subsystem ──")

flow_items = [
    ("Func. Generator\n(Flow Input 1)", C_SENSOR, 9.1),
    ("Flow Input (RB0)",                 C_FLOW,   8.3),
    ("PIC18F2580\nEmbedded Controller",  C_MCU,    7.4),
    ("Flow Input (RB1)",                 C_FLOW,   6.5),
    ("Func. Generator\n(Flow Input 2)", C_SENSOR, 5.7),
]

for lbl, col, y in flow_items:
    h = BH * 1.5 if "\n" in lbl else BH
    box(ax, CX1, y, BW, h, lbl, col)

# arrows
pairs = [(0, 1), (1, 2), (3, 2), (4, 3)]   # (from_idx, to_idx)
ys = [y for _, _, y in flow_items]
heights = [BH * 1.5 if "\n" in lbl else BH for lbl, _, _ in flow_items]

for fi, ti in pairs:
    fy, fh = ys[fi], heights[fi]
    ty, th = ys[ti], heights[ti]
    if fy > ty:
        arr(ax, CX1, fy - fh / 2 - 0.04, CX1, ty + th / 2 + 0.04)
    else:
        arr(ax, CX1, fy + fh / 2 + 0.04, CX1, ty - th / 2 - 0.04)

# ===========================================================================
# COLUMN 2 – Acoustic Channel A  (x = 7.0)
# ===========================================================================
CX2 = 7.0
panel(ax, CX2 - 1.55, 1.8, 3.1, 7.7)
section_label(ax, CX2, 9.55, "── Acoustic Channel A ──")

ch_a = [
    ("Acoustic Sensor A",               C_SENSOR, 9.1),
    ("LM386 Amplifier",                 C_COND,   8.3),
    ("Twin-T Notch Filter  50 Hz",      C_COND,   7.5),
    ("Sallen-Key BPF  ~1 kHz",          C_COND,   6.7),
    ("ADC  AN0",                        C_ADC,    5.9),
]

for lbl, col, y in ch_a:
    box(ax, CX2, y, BW, BH, lbl, col)

for i in range(len(ch_a) - 1):
    _, _, y1 = ch_a[i]
    _, _, y2 = ch_a[i + 1]
    arr(ax, CX2, y1 - BH / 2 - 0.04, CX2, y2 + BH / 2 + 0.04)

# ===========================================================================
# COLUMN 3 – Acoustic Channel B  (x = 11.3)
# ===========================================================================
CX3 = 11.3
panel(ax, CX3 - 1.55, 1.8, 3.1, 7.7)
section_label(ax, CX3, 9.55, "── Acoustic Channel B ──")

ch_b = [
    ("Acoustic Sensor B",               C_SENSOR, 9.1),
    ("LM386 Amplifier",                 C_COND,   8.3),
    ("Twin-T Notch Filter  50 Hz",      C_COND,   7.5),
    ("Sallen-Key BPF  ~1 kHz",          C_COND,   6.7),
    ("ADC  AN1",                        C_ADC,    5.9),
]

for lbl, col, y in ch_b:
    box(ax, CX3, y, BW, BH, lbl, col)

# arrows flow upward toward MCU (bottom up from sensor)
for i in range(len(ch_b) - 1):
    _, _, y1 = ch_b[i]
    _, _, y2 = ch_b[i + 1]
    arr(ax, CX3, y1 - BH / 2 - 0.04, CX3, y2 + BH / 2 + 0.04)

# ===========================================================================
# SHARED MCU block – centred between CH A and CH B
# ===========================================================================
MCU_X = 9.15
MCU_Y = 4.7
MCU_W = 5.6
MCU_H = 0.75

mcu_patch = FancyBboxPatch(
    (MCU_X - MCU_W / 2, MCU_Y - MCU_H / 2), MCU_W, MCU_H,
    boxstyle="round,pad=0.08",
    linewidth=1.5,
    edgecolor=C_MCU,
    facecolor="#2a0a0a",
    zorder=3,
)
ax.add_patch(mcu_patch)
ax.text(MCU_X, MCU_Y,
        "PIC18F2580  —  Cross-Correlation & TDOA Processing",
        ha="center", va="center",
        fontsize=9, color=C_MCU, fontweight="bold",
        fontfamily="monospace", zorder=5)

# Arrows from CH A bottom → MCU left side
arr(ax, CX2, ch_a[-1][2] - BH / 2 - 0.04, CX2, MCU_Y + MCU_H / 2 + 0.04)
# Arrows from CH B bottom → MCU right side
arr(ax, CX3, ch_b[-1][2] - BH / 2 - 0.04, CX3, MCU_Y + MCU_H / 2 + 0.04)

# ===========================================================================
# OUTPUT Subsystem
# ===========================================================================
OUT_Y  = 3.5
out_items = [
    ("LCD Display",          C_OUT, 5.5),
    ("LED Indicators",       C_OUT, 9.15),
    ("UART Serial Monitor",  C_OUT, 12.8),
]

section_label(ax, MCU_X, OUT_Y + 0.65, "── Output Subsystem ──")

for lbl, col, ox in out_items:
    box(ax, ox, OUT_Y, BW, BH, lbl, col)
    arr(ax, MCU_X, MCU_Y - MCU_H / 2 - 0.04, ox, OUT_Y + BH / 2 + 0.04)

# ===========================================================================
# Legend
# ===========================================================================
legend_entries = [
    (C_SENSOR, "Sensor / Signal Source"),
    (C_COND,   "Signal Conditioning"),
    (C_ADC,    "ADC Channel"),
    (C_MCU,    "MCU / Processing"),
    (C_OUT,    "Output Subsystem"),
]
patches = [
    mpatches.Patch(facecolor=BG_PANEL, edgecolor=c, label=l, linewidth=1.5)
    for c, l in legend_entries
]
leg = ax.legend(
    handles=patches,
    loc="lower left",
    fontsize=7.5,
    framealpha=0.9,
    facecolor=BG_PANEL,
    edgecolor=BORDER,
    ncol=1,
    bbox_to_anchor=(0.01, 0.01),
)
for text in leg.get_texts():
    text.set_color(C_TITLE)
    text.set_fontfamily("monospace")

# ===========================================================================
# Save
# ===========================================================================
results_dir = Path(__file__).resolve().parents[2] / "results"
results_dir.mkdir(exist_ok=True)
out_path = results_dir / "system_architecture.png"

plt.tight_layout(pad=0.4)
plt.savefig(out_path, dpi=180, bbox_inches="tight",
            facecolor=fig.get_facecolor())
print(f"Saved → {out_path}")
plt.show()
