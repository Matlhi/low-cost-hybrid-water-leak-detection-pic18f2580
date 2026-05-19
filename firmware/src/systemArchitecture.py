"""
system_architecture_diagram.py
Generates a diagram image of the hybrid embedded water leak detection
and localisation system architecture using matplotlib.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def draw_box(ax, x, y, w, h, label, color, text_color="white", fontsize=8.5):
    box = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.04",
        linewidth=1.2,
        edgecolor="#333333",
        facecolor=color,
        zorder=3,
    )
    ax.add_patch(box)
    ax.text(
        x, y, label,
        ha="center", va="center",
        fontsize=fontsize, color=text_color,
        fontweight="bold", zorder=4,
        multialignment="center",
    )


def arrow(ax, x1, y1, x2, y2, color="#444444"):
    ax.annotate(
        "",
        xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=1.4,
        ),
        zorder=2,
    )


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
C_SENSOR  = "#1a6faf"   # blue  – sensors / function generators
C_COND    = "#2e8b57"   # green – signal conditioning
C_ADC     = "#8b4513"   # brown – ADC channels
C_MCU     = "#8b0000"   # dark red – PIC18F2580 blocks
C_OUT     = "#4b0082"   # indigo – output subsystem
C_FLOW_IN = "#1a6faf"
C_LABEL   = "#555555"   # section label colour

BW  = 2.4   # box width
BH  = 0.52  # box height
GAP = 0.88  # vertical gap between box centres

# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(14, 11))
ax.set_xlim(0, 14)
ax.set_ylim(0, 11)
ax.axis("off")
fig.patch.set_facecolor("#f7f9fc")
ax.set_facecolor("#f7f9fc")

ax.text(7, 10.6, "Hybrid Embedded Water Leak Detection & Localisation System",
        ha="center", va="center", fontsize=13, fontweight="bold", color="#1a1a2e")

# ===========================================================================
# COLUMN 1 – Flow Subsystem  (x ≈ 2.8)
# ===========================================================================
CX = 2.8
label_y = 10.15

ax.text(CX, label_y, "Flow Monitoring Subsystem",
        ha="center", va="center", fontsize=9, color=C_LABEL,
        fontstyle="italic")

flow_items = [
    ("Simulated Flow\nInput 1\n(Function Generator)", C_SENSOR),
    ("Flow Monitoring\nInput (RB0)",                   C_FLOW_IN),
    ("PIC18F2580\nEmbedded Controller",                C_MCU),
    ("Flow Monitoring\nInput (RB1)",                   C_FLOW_IN),
    ("Simulated Flow\nInput 2\n(Function Generator)",  C_SENSOR),
]

flow_y = [9.55, 8.65, 7.75, 6.85, 5.95]

for (lbl, col), y in zip(flow_items, flow_y):
    h = BH * 1.5 if "\n" in lbl and lbl.count("\n") >= 2 else BH
    draw_box(ax, CX, y, BW, h, lbl, col)

# Arrows (downward for top pair, upward for bottom pair)
for i in range(len(flow_y) - 1):
    y_start = flow_y[i] - BH / 2 - 0.05
    y_end   = flow_y[i + 1] + BH / 2 + 0.05
    if i < 2:
        arrow(ax, CX, y_start, CX, y_end)   # downward
    else:
        arrow(ax, CX, y_end,   CX, y_start) # upward (reversed)

# ===========================================================================
# COLUMN 2 – Channel A  (x ≈ 7.0)
# ===========================================================================
CXA = 7.0

ax.text(CXA, label_y, "Acoustic Channel A",
        ha="center", va="center", fontsize=9, color=C_LABEL,
        fontstyle="italic")

ch_a_items = [
    ("Acoustic Sensor A",                    C_SENSOR),
    ("LM386 Amplifier",                      C_COND),
    ("Twin-T Notch Filter\n(50 Hz)",         C_COND),
    ("Sallen-Key Bandpass\nFilter (~1 kHz)", C_COND),
    ("ADC Channel AN0",                      C_ADC),
    ("PIC18F2580\nCross-Correlation\n& TDOA Processing", C_MCU),
]

ch_a_y = [9.55, 8.65, 7.75, 6.85, 5.95, 5.05]

for (lbl, col), y in zip(ch_a_items, ch_a_y):
    h = BH * 1.6 if lbl.count("\n") >= 2 else BH
    draw_box(ax, CXA, y, BW, h, lbl, col)

for i in range(len(ch_a_y) - 1):
    y_start = ch_a_y[i] - BH / 2 - 0.05
    y_end   = ch_a_y[i + 1] + BH / 2 + 0.05
    arrow(ax, CXA, y_start, CXA, y_end)

# ===========================================================================
# COLUMN 3 – Channel B  (x ≈ 11.2)
# ===========================================================================
CXB = 11.2

ax.text(CXB, label_y, "Acoustic Channel B",
        ha="center", va="center", fontsize=9, color=C_LABEL,
        fontstyle="italic")

# Channel B is the mirror of A (bottom-up)
ch_b_labels = [
    ("PIC18F2580\nCross-Correlation\n& TDOA Processing", C_MCU),
    ("ADC Channel AN1",                      C_ADC),
    ("Sallen-Key Bandpass\nFilter (~1 kHz)", C_COND),
    ("Twin-T Notch Filter\n(50 Hz)",         C_COND),
    ("LM386 Amplifier",                      C_COND),
    ("Acoustic Sensor B",                    C_SENSOR),
]

ch_b_y = [5.05, 5.95, 6.85, 7.75, 8.65, 9.55]

for (lbl, col), y in zip(ch_b_labels, ch_b_y):
    h = BH * 1.6 if lbl.count("\n") >= 2 else BH
    draw_box(ax, CXB, y, BW, h, lbl, col)

# Arrows go upward (sensor B feeds upward into MCU)
for i in range(len(ch_b_y) - 1):
    y_lo = ch_b_y[i]
    y_hi = ch_b_y[i + 1]
    arrow(ax, CXB, y_lo + BH / 2 + 0.05, CXB, y_hi - BH / 2 - 0.05)

# ===========================================================================
# OUTPUT Subsystem – centred below Channel A MCU block
# ===========================================================================
out_cx = 7.0
out_y_start = 5.05 - BH * 1.6 / 2 - 0.15  # below the MCU box

ax.text(out_cx, out_y_start - 0.15,
        "Output Subsystem",
        ha="center", va="top", fontsize=9, color=C_LABEL, fontstyle="italic")

out_items = [
    ("LCD Display",          C_OUT, 5.4),
    ("LED Indicators",       C_OUT, 7.0),
    ("UART Serial Monitor",  C_OUT, 8.6),
]

out_y = out_y_start - 0.55

# Horizontal fan-out from MCU bottom to three output boxes
mcu_bottom = 5.05 - BH * 1.6 / 2
for lbl, col, ox in out_items:
    draw_box(ax, ox, out_y, BW, BH, lbl, col)
    ax.annotate(
        "",
        xy=(ox, out_y + BH / 2),
        xytext=(CXA, mcu_bottom),
        arrowprops=dict(
            arrowstyle="-|>",
            color="#444444",
            lw=1.2,
            connectionstyle="arc3,rad=0.0",
        ),
        zorder=2,
    )

# ===========================================================================
# Legend
# ===========================================================================
legend_items = [
    (C_SENSOR, "Sensor / Signal Source"),
    (C_COND,   "Signal Conditioning"),
    (C_ADC,    "ADC Channel"),
    (C_MCU,    "PIC18F2580 Processing"),
    (C_OUT,    "Output Subsystem"),
]
patches = [mpatches.Patch(facecolor=c, edgecolor="#333333", label=l)
           for c, l in legend_items]
ax.legend(
    handles=patches,
    loc="lower left",
    fontsize=8,
    framealpha=0.85,
    edgecolor="#cccccc",
    ncol=1,
)

# ---------------------------------------------------------------------------
# Save to results folder
# ---------------------------------------------------------------------------
results_dir = Path(__file__).resolve().parents[2] / "results"
results_dir.mkdir(exist_ok=True)
out_path = results_dir / "system_architecture.png"

plt.tight_layout()
plt.savefig(out_path, dpi=180, bbox_inches="tight",
            facecolor=fig.get_facecolor())
print(f"Saved {out_path}")
plt.show()
