"""
flowchart.py
Operational flowchart for the hybrid embedded water leak detection
and localisation system. Outputs to results/flowchart.png.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from pathlib import Path
import numpy as np

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
BG       = "#0d1117"
BG_PANEL = "#161b22"
BORDER   = "#30363d"

C_TERM  = "#58a6ff"
C_PROC  = "#1f6feb"
C_ADC   = "#e3b341"
C_MCU   = "#f85149"
C_DEC   = "#bc8cff"
C_OUT   = "#79c0ff"
C_FLOW  = "#ffa657"
C_ARROW = "#8b949e"
C_TITLE = "#e6edf3"
C_LABEL = "#8b949e"
C_YES   = "#3fb950"

# ---------------------------------------------------------------------------
# Layout  (1 data unit = 1 inch at figsize 20x50)
# ---------------------------------------------------------------------------
CX       = 10.0
MAIN_W   = 10.0
MAIN_H   = 1.5
DIA_W    = 7.0
DIA_H    = 1.9
BRANCH_W = 5.0
BRANCH_H = 1.5
TERM_W   = 4.5
TERM_H   = 1.0
FLAG_X   = 16.8
ALERT_X  = 3.2
LOOP_X   = 0.3
GAP_PROC = 3.0
GAP_DEC  = 3.4

FS_MAIN   = 28
FS_BRANCH = 24
FS_DIA    = 26
FS_TERM   = 34
FS_ARROW  = 20
FS_TITLE  = 22

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def process_box(ax, x, y, w, h, label, fc, fontsize=FS_MAIN):
    ax.add_patch(FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.12",
        linewidth=1.8, edgecolor=fc,
        facecolor=BG_PANEL, zorder=3,
    ))
    ax.add_patch(FancyBboxPatch(
        (x - w / 2, y - h / 2), 0.14, h,
        boxstyle="round,pad=0.0",
        linewidth=0, facecolor=fc, zorder=4,
    ))
    ax.text(x + 0.10, y, label,
            ha="center", va="center",
            fontsize=fontsize, color=C_TITLE,
            fontweight="bold", zorder=5,
            multialignment="center",
            linespacing=1.55)


def terminal(ax, x, y, w, h, label, fc=C_TERM):
    ax.add_patch(FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.30",
        linewidth=2.6, edgecolor=fc,
        facecolor=fc + "22", zorder=3,
    ))
    ax.text(x, y, label,
            ha="center", va="center",
            fontsize=FS_TERM, color=fc,
            fontweight="bold", zorder=5)


def diamond(ax, x, y, w, h, label, fc=C_DEC):
    hw, hh = w / 2, h / 2
    pts = np.array([[x, y + hh], [x + hw, y], [x, y - hh], [x - hw, y]])
    ax.add_patch(plt.Polygon(pts, closed=True,
                             linewidth=2.0, edgecolor=fc,
                             facecolor=BG_PANEL, zorder=3))
    ax.text(x, y, label,
            ha="center", va="center",
            fontsize=FS_DIA, color=fc,
            fontweight="bold", zorder=5,
            multialignment="center",
            linespacing=1.55)


def arr(ax, x1, y1, x2, y2, color=C_ARROW, label="", label_side="right"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=2.2, mutation_scale=22), zorder=2)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx = 0.42 if label_side == "right" else -0.42
        ax.text(mx + dx, my, label,
                ha="center", va="center",
                fontsize=FS_ARROW, color=color,
                fontweight="bold", zorder=6)


def elbow(ax, x1, y1, x2, y2, color=C_ARROW, label="", label_side="top"):
    ax.annotate("", xy=(x2, y1), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-", color=color, lw=2.2), zorder=2)
    ax.annotate("", xy=(x2, y2), xytext=(x2, y1),
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=2.2, mutation_scale=22), zorder=2)
    if label:
        lx = (x1 + x2) / 2
        dy = 0.34 if label_side == "top" else -0.34
        ax.text(lx, y1 + dy, label,
                ha="center", va="center",
                fontsize=FS_ARROW, color=color,
                fontweight="bold", zorder=6)


# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(20, 37))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 20)
ax.set_ylim(0, 37)
ax.axis("off")

ax.text(10, 36.55,
        "Hybrid Water Leak Detection & Localisation System",
        ha="center", va="center",
        fontsize=FS_TITLE, fontweight="bold",
        color=C_TITLE, zorder=6)
ax.text(10, 36.0,
        "Operational Flowchart  -  PIC18F2580  -  Firmware Logic",
        ha="center", va="center",
        fontsize=FS_TITLE - 6, color=C_LABEL, zorder=6)
ax.plot([0.4, 19.6], [35.6, 35.6], color=BORDER, lw=1.2)

# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------
Y = 35.1

# 1. START
SY = Y
terminal(ax, CX, SY, TERM_W, TERM_H, "START")
Y -= GAP_PROC

# 2. Initialise
IY = Y
process_box(ax, CX, IY, MAIN_W, MAIN_H,
            "Initialise PIC18F2580\nADC  UART  LCD  Timers  Interrupts",
            C_PROC)
arr(ax, CX, SY - TERM_H / 2, CX, IY + MAIN_H / 2)
Y -= GAP_PROC

# 3. Read flow inputs
FRY = Y
process_box(ax, CX, FRY, MAIN_W, MAIN_H,
            "Read Flow Inputs\nRB0 via Gen 1    RB1 via Gen 2",
            C_FLOW)
arr(ax, CX, IY - MAIN_H / 2, CX, FRY + MAIN_H / 2)
Y -= GAP_DEC

# 4. Flow anomaly decision
FDY = Y
diamond(ax, CX, FDY, DIA_W, DIA_H, "Flow\nAnomaly?", C_DEC)
arr(ax, CX, FRY - MAIN_H / 2, CX, FDY + DIA_H / 2)
Y -= GAP_DEC

# 4a. YES branch — right
FLAG_Y = FDY
process_box(ax, FLAG_X, FLAG_Y, BRANCH_W, BRANCH_H,
            "Set Flow Alert Flag\nLog Event via UART",
            C_FLOW, fontsize=FS_BRANCH)
elbow(ax, CX + DIA_W / 2, FDY,
      FLAG_X - BRANCH_W / 2, FLAG_Y,
      color=C_YES, label="YES", label_side="top")

# 5. Sample ADC
CAY = Y
process_box(ax, CX, CAY, MAIN_W, MAIN_H,
            "Sample ADC Channels\nAN0  Sensor A    AN1  Sensor B",
            C_ADC)
arr(ax, CX, FDY - DIA_H / 2, CX, CAY + MAIN_H / 2,
    label="NO", label_side="right")
elbow(ax, FLAG_X, FLAG_Y - BRANCH_H / 2,
      CX + MAIN_W / 2, CAY, color=C_FLOW)
Y -= GAP_PROC

# 6. Cross-correlation
CCY = Y
process_box(ax, CX, CCY, MAIN_W, MAIN_H,
            "Compute Cross-Correlation\nChannel A  x  Channel B",
            C_MCU)
arr(ax, CX, CAY - MAIN_H / 2, CX, CCY + MAIN_H / 2)
Y -= GAP_PROC

# 7. Extract TDOA
TY = Y
process_box(ax, CX, TY, MAIN_W, MAIN_H,
            "Extract Peak Lag  ->  TDOA\nTime Difference of Arrival",
            C_MCU)
arr(ax, CX, CCY - MAIN_H / 2, CX, TY + MAIN_H / 2)
Y -= GAP_PROC

# 8. Calculate position
PY = Y
process_box(ax, CX, PY, MAIN_W, MAIN_H,
            "Calculate Leak Position\nx  =  v  *  TDOA  /  2",
            C_MCU)
arr(ax, CX, TY - MAIN_H / 2, CX, PY + MAIN_H / 2)
Y -= GAP_DEC

# 9. Leak detected?
LDY = Y
diamond(ax, CX, LDY, DIA_W, DIA_H, "Leak\nDetected?", C_DEC)
arr(ax, CX, PY - MAIN_H / 2, CX, LDY + DIA_H / 2)
Y -= GAP_DEC

# 9a. YES branch — left
ALERT_Y = LDY
process_box(ax, ALERT_X, ALERT_Y, BRANCH_W, BRANCH_H,
            "Output Alert\nLCD  LED:RED  UART",
            C_OUT, fontsize=FS_BRANCH)
elbow(ax, CX - DIA_W / 2, LDY,
      ALERT_X + BRANCH_W / 2, ALERT_Y,
      color=C_YES, label="YES", label_side="top")

# 10. No-leak status
NSY = Y
process_box(ax, CX, NSY, MAIN_W, MAIN_H,
            "No Leak — Update Status\nLCD:OK  LED:GREEN  UART:log",
            C_OUT)
arr(ax, CX, LDY - DIA_H / 2, CX, NSY + MAIN_H / 2,
    label="NO", label_side="right")
elbow(ax, ALERT_X, ALERT_Y - BRANCH_H / 2,
      CX - MAIN_W / 2, NSY, color=C_OUT)
Y -= GAP_PROC

# 11. Wait / next cycle
WY = Y
process_box(ax, CX, WY, MAIN_W, MAIN_H,
            "Wait for Next Sample Period\nTimer Interrupt / Polling Delay",
            C_PROC)
arr(ax, CX, NSY - MAIN_H / 2, CX, WY + MAIN_H / 2)
Y -= 2.0

# 12. Loop-back rail
STUB_Y = Y + 0.1
arr(ax, CX, WY - MAIN_H / 2, CX, STUB_Y)
ax.annotate("", xy=(LOOP_X, STUB_Y), xytext=(CX, STUB_Y),
            arrowprops=dict(arrowstyle="-", color=C_ARROW, lw=2.2), zorder=2)
ax.annotate("", xy=(LOOP_X, FRY), xytext=(LOOP_X, STUB_Y),
            arrowprops=dict(arrowstyle="-", color=C_ARROW, lw=2.2), zorder=2)
ax.annotate("", xy=(CX - MAIN_W / 2, FRY), xytext=(LOOP_X, FRY),
            arrowprops=dict(arrowstyle="-|>", color=C_ARROW,
                            lw=2.2, mutation_scale=22), zorder=2)
ax.text(LOOP_X - 0.3, (FRY + STUB_Y) / 2, "loop",
        ha="right", va="center",
        fontsize=FS_ARROW, color=C_LABEL,
        fontstyle="italic", zorder=6)

Y -= 1.2

# 13. END
terminal(ax, CX, Y, TERM_W, TERM_H, "END")

# ---------------------------------------------------------------------------
# Legend
# ---------------------------------------------------------------------------
entries = [
    (C_TERM, "Terminal (Start / End)"),
    (C_PROC, "Initialise / Wait"),
    (C_FLOW, "Flow Monitoring"),
    (C_ADC,  "ADC Sampling"),
    (C_MCU,  "DSP / Computation"),
    (C_DEC,  "Decision"),
    (C_OUT,  "Output / Alert"),
]
patches = [mpatches.Patch(facecolor=BG_PANEL, edgecolor=c,
                           label=l, linewidth=2.0)
           for c, l in entries]
leg = ax.legend(handles=patches, loc="lower right",
                fontsize=14, framealpha=0.92,
                facecolor=BG_PANEL, edgecolor=BORDER,
                ncol=1, bbox_to_anchor=(0.995, 0.005))
for t in leg.get_texts():
    t.set_color(C_TITLE)

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
results_dir = Path(__file__).resolve().parents[2] / "results"
results_dir.mkdir(exist_ok=True)
out_path = results_dir / "flowchart.png"

plt.tight_layout(pad=0.4)
plt.savefig(out_path, dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
print(f"Saved -> {out_path}")
plt.show()
