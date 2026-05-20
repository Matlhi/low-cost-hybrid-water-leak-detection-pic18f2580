"""
blockDiagram.py
Block diagram of the hybrid embedded water leak detection and
localisation system. Outputs to results/block_diagram.png.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from pathlib import Path

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
BG       = "#0d1117"
BG_PANEL = "#161b22"
BORDER   = "#30363d"

C_SENSOR = "#58a6ff"
C_COND   = "#3fb950"
C_ADC    = "#e3b341"
C_MCU    = "#f85149"
C_FLOW   = "#58a6ff"
C_OUT    = "#bc8cff"
C_ARROW  = "#8b949e"
C_TITLE  = "#e6edf3"
C_LABEL  = "#8b949e"

BW = 2.5
BH = 0.50

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def box(ax, x, y, w, h, label, fc, fontsize=8.0):
    ax.add_patch(FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.06",
        linewidth=1.0, edgecolor=fc,
        facecolor=BG_PANEL, zorder=3, clip_on=False,
    ))
    ax.add_patch(FancyBboxPatch(
        (x - w / 2, y - h / 2), 0.07, h,
        boxstyle="round,pad=0.0",
        linewidth=0, facecolor=fc, zorder=4, clip_on=False,
    ))
    ax.text(x + 0.05, y, label,
            ha="center", va="center",
            fontsize=fontsize, color=C_TITLE,
            fontweight="bold", zorder=5,
            multialignment="center", fontfamily="monospace")


def arr(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=C_ARROW,
                                lw=1.2, mutation_scale=10), zorder=2)


def col_panel(ax, cx, y_bot, height):
    ax.add_patch(FancyBboxPatch(
        (cx - 1.55, y_bot), 3.1, height,
        boxstyle="round,pad=0.1",
        linewidth=1.0, edgecolor=BORDER,
        facecolor="#1a2030", zorder=1, alpha=0.45,
    ))


def col_label(ax, x, y, text):
    ax.text(x, y, text, ha="center", va="center",
            fontsize=7.8, color=C_LABEL,
            fontstyle="italic", fontfamily="monospace", zorder=5)


# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(17, 11))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 17)
ax.set_ylim(0, 11)
ax.axis("off")

ax.text(8.5, 10.6,
        "Hybrid Embedded Water Leak Detection & Localisation System",
        ha="center", va="center",
        fontsize=13.5, fontweight="bold",
        color=C_TITLE, fontfamily="monospace", zorder=6)
ax.text(8.5, 10.2,
        "System Block Diagram  ·  PIC18F2580  ·  Acoustic TDOA  ·  Flow Monitoring",
        ha="center", va="center",
        fontsize=8.2, color=C_LABEL, fontfamily="monospace", zorder=6)
ax.plot([0.5, 16.5], [9.9, 9.9], color=BORDER, lw=0.8, zorder=2)

# ===========================================================================
# COLUMN 1 – Flow Subsystem  x=2.7
# ===========================================================================
CX1 = 2.7
col_panel(ax, CX1, 2.1, 7.5)
col_label(ax, CX1, 9.65, "── Flow Monitoring Subsystem ──")

flow_stack = [
    ("Func. Generator\n(Flow Input 1)", C_SENSOR, 9.2,  BH * 1.5),
    ("Flow Input  RB0",                  C_FLOW,   8.35, BH),
    ("PIC18F2580\nEmbedded Controller",  C_MCU,    7.45, BH * 1.5),
    ("Flow Input  RB1",                  C_FLOW,   6.6,  BH),
    ("Func. Generator\n(Flow Input 2)", C_SENSOR, 5.75, BH * 1.5),
]

for lbl, col, y, h in flow_stack:
    box(ax, CX1, y, BW, h, lbl, col)

# arrows: top two down, bottom two up toward MCU
for (_, _, ya, ha_), (_, _, yb, hb) in zip(flow_stack[:2], flow_stack[1:3]):
    arr(ax, CX1, ya - ha_ / 2 - 0.04, CX1, yb + hb / 2 + 0.04)
for (_, _, ya, ha_), (_, _, yb, hb) in zip(flow_stack[4:2:-1], flow_stack[3:1:-1]):
    arr(ax, CX1, ya + ha_ / 2 + 0.04, CX1, yb - hb / 2 - 0.04)

# ===========================================================================
# COLUMN 2 – Acoustic Channel A  x=7.2
# ===========================================================================
CX2 = 7.2
col_panel(ax, CX2, 2.1, 7.5)
col_label(ax, CX2, 9.65, "── Acoustic Channel A ──")

ch_a = [
    ("Acoustic Sensor A",          C_SENSOR, 9.2),
    ("LM386 Amplifier",            C_COND,   8.4),
    ("Twin-T Notch Filter  50 Hz", C_COND,   7.6),
    ("Sallen-Key BPF  ~1 kHz",     C_COND,   6.8),
    ("ADC Channel  AN0",           C_ADC,    6.0),
]

for lbl, col, y in ch_a:
    box(ax, CX2, y, BW, BH, lbl, col)

for (_, _, y1), (_, _, y2) in zip(ch_a, ch_a[1:]):
    arr(ax, CX2, y1 - BH / 2 - 0.04, CX2, y2 + BH / 2 + 0.04)

# ===========================================================================
# COLUMN 3 – Acoustic Channel B  x=11.7
# ===========================================================================
CX3 = 11.7
col_panel(ax, CX3, 2.1, 7.5)
col_label(ax, CX3, 9.65, "── Acoustic Channel B ──")

ch_b = [
    ("Acoustic Sensor B",          C_SENSOR, 9.2),
    ("LM386 Amplifier",            C_COND,   8.4),
    ("Twin-T Notch Filter  50 Hz", C_COND,   7.6),
    ("Sallen-Key BPF  ~1 kHz",     C_COND,   6.8),
    ("ADC Channel  AN1",           C_ADC,    6.0),
]

for lbl, col, y in ch_b:
    box(ax, CX3, y, BW, BH, lbl, col)

for (_, _, y1), (_, _, y2) in zip(ch_b, ch_b[1:]):
    arr(ax, CX3, y1 - BH / 2 - 0.04, CX3, y2 + BH / 2 + 0.04)

# ===========================================================================
# Shared MCU – centred between columns 2 & 3
# ===========================================================================
MCU_X = 9.45
MCU_Y = 4.65
MCU_W = 6.0
MCU_H = 0.78

ax.add_patch(FancyBboxPatch(
    (MCU_X - MCU_W / 2, MCU_Y - MCU_H / 2), MCU_W, MCU_H,
    boxstyle="round,pad=0.08",
    linewidth=1.8, edgecolor=C_MCU,
    facecolor="#1a0505", zorder=3,
))
ax.text(MCU_X, MCU_Y,
        "PIC18F2580  —  Cross-Correlation & TDOA Processing",
        ha="center", va="center",
        fontsize=9, color=C_MCU,
        fontweight="bold", fontfamily="monospace", zorder=5)

# CH A → MCU
arr(ax, CX2, ch_a[-1][2] - BH / 2 - 0.04, CX2, MCU_Y + MCU_H / 2 + 0.04)
# CH B → MCU
arr(ax, CX3, ch_b[-1][2] - BH / 2 - 0.04, CX3, MCU_Y + MCU_H / 2 + 0.04)

# ===========================================================================
# Output Subsystem
# ===========================================================================
OUT_Y = 3.45
col_label(ax, MCU_X, OUT_Y + 0.72, "── Output Subsystem ──")

out_items = [
    ("LCD Display",         C_OUT, 6.1),
    ("LED Indicators",      C_OUT, 9.45),
    ("UART Serial Monitor", C_OUT, 12.8),
]

for lbl, col, ox in out_items:
    box(ax, ox, OUT_Y, BW, BH, lbl, col)
    arr(ax, MCU_X, MCU_Y - MCU_H / 2 - 0.04, ox, OUT_Y + BH / 2 + 0.04)

# ===========================================================================
# Legend
# ===========================================================================
entries = [
    (C_SENSOR, "Sensor / Signal Source"),
    (C_COND,   "Signal Conditioning"),
    (C_ADC,    "ADC Channel"),
    (C_MCU,    "MCU / Processing"),
    (C_OUT,    "Output Subsystem"),
]
patches = [mpatches.Patch(facecolor=BG_PANEL, edgecolor=c,
                           label=l, linewidth=1.5)
           for c, l in entries]
leg = ax.legend(handles=patches, loc="lower left", fontsize=7.5,
                framealpha=0.9, facecolor=BG_PANEL, edgecolor=BORDER,
                ncol=1, bbox_to_anchor=(0.01, 0.01))
for t in leg.get_texts():
    t.set_color(C_TITLE)
    t.set_fontfamily("monospace")

# ===========================================================================
# Save
# ===========================================================================
results_dir = Path(__file__).resolve().parents[2] / "results"
results_dir.mkdir(exist_ok=True)
out_path = results_dir / "block_diagram.png"

plt.tight_layout(pad=0.4)
plt.savefig(out_path, dpi=180, bbox_inches="tight",
            facecolor=fig.get_facecolor())
print(f"Saved -> {out_path}")
plt.show()
