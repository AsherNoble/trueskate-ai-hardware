import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE  = "#fcfcfb"
CMD      = "#2a78d6"   # categorical slot 1 - commanded
MEAS     = "#eb6834"   # categorical slot 2 - measured
INK      = "#1a1a19"
MUTED    = "#6b6b68"
GRID     = "#e6e6e3"

def load(path):
    t, tgt, ang, uq = [], [], [], []
    for line in open(path, errors="replace"):
        line = line.strip()
        if not line or line.startswith("#") or line[0].isalpha():
            continue
        p = line.split(",")
        if len(p) != 7:
            continue
        try:
            t.append(float(p[0])/1000.0); tgt.append(float(p[3]))
            ang.append(float(p[4])); uq.append(float(p[6]))
        except ValueError:
            pass
    return t, tgt, ang, uq

def style(ax):
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)

def plot(path, out, title, sub, vlim, xlim=None):
    t, tgt, ang, uq = load(path)
    fig, (ax, ax2) = plt.subplots(
        2, 1, figsize=(11, 6.2), sharex=True,
        gridspec_kw=dict(height_ratios=[3, 1], hspace=0.12))
    fig.patch.set_facecolor(SURFACE)

    ax.plot(t, tgt, color=CMD, linewidth=2.0, label="commanded", zorder=3)
    ax.plot(t, ang, color=MEAS, linewidth=2.0, label="measured", zorder=4)
    style(ax)
    ax.set_ylabel("angle (deg)", color=MUTED, fontsize=10)
    ax.set_title(title, color=INK, fontsize=14, weight="bold", loc="left", pad=14)
    ax.text(0, 1.015, sub, transform=ax.transAxes, color=MUTED,
            fontsize=10, va="bottom")
    leg = ax.legend(frameon=False, loc="upper right", fontsize=10,
                    labelcolor=MUTED, ncol=2)

    ax2.plot(t, uq, color=MUTED, linewidth=1.6, zorder=3)
    ax2.axhline(vlim,  color="#d03b3b", linewidth=1.2, linestyle="--", zorder=2)
    ax2.axhline(-vlim, color="#d03b3b", linewidth=1.2, linestyle="--", zorder=2)
    ax2.text(t[-1], vlim, f" limit {vlim:g} V", color="#d03b3b",
             fontsize=9, va="center", ha="left", clip_on=False)
    style(ax2)
    ax2.set_ylabel("Uq (V)", color=MUTED, fontsize=10)
    ax2.set_xlabel("time (s)", color=MUTED, fontsize=10)
    ax2.set_ylim(-vlim*1.45, vlim*1.45)

    if xlim:
        ax.set_xlim(*xlim)
    fig.subplots_adjust(left=0.075, right=0.90, top=0.86, bottom=0.10)
    fig.savefig(out, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    print("wrote", out)

plot("step_2v.csv", "step_2v.png",
     "Step response — 90° out and back",
     "axis 1, voltage_limit 2 V, angle mode, 1 kHz log", 2.0)
plot("flick_2v.csv", "flick_2v.png",
     "Single flick — 60° out and straight back",
     "axis 1, voltage_limit 2 V, full cycle 413 ms", 2.0)
plot("flick20_2v.csv", "flick20_2v.png",
     "Twenty consecutive flicks — repeatability",
     "axis 1, voltage_limit 2 V, 13.5 s continuous", 2.0)

# First vs last flick overlaid: the drift question, answered directly.
t, tgt, ang, uq = load("flick20_2v.csv")
rows = list(zip(t, tgt, ang))
def flick_window(n):
    # phase/flick columns dropped by load(); re-read to segment
    seg = []
    for line in open("flick20_2v.csv", errors="replace"):
        line = line.strip()
        if not line or line.startswith("#") or line[0].isalpha(): continue
        p = line.split(",")
        if len(p) != 7: continue
        if int(p[2]) == n and int(p[1]) in (1, 2):
            seg.append((float(p[0]), float(p[3]), float(p[4])))
    if not seg: return None
    t0 = seg[0][0]; base = seg[0][2]
    return [(s[0]-t0, s[1]-base, s[2]-base) for s in seg]

fig, ax = plt.subplots(figsize=(11, 4.6))
fig.patch.set_facecolor(SURFACE)
f1, f20 = flick_window(1), flick_window(20)
ax.plot([p[0] for p in f1], [p[1] for p in f1], color=MUTED,
        linewidth=1.4, linestyle="--", zorder=2, label="commanded")
ax.plot([p[0] for p in f1],  [p[2] for p in f1],  color=CMD,
        linewidth=2.0, zorder=3, label="flick 1")
ax.plot([p[0] for p in f20], [p[2] for p in f20], color=MEAS,
        linewidth=2.0, zorder=4, label="flick 20")
style(ax)
ax.set_title("Flick 1 vs flick 20 — thermal drift check", color=INK,
             fontsize=14, weight="bold", loc="left", pad=14)
ax.text(0, 1.02, "overlaid from each flick's own start; 13.5 s of continuous duty between them",
        transform=ax.transAxes, color=MUTED, fontsize=10, va="bottom")
ax.set_xlabel("time within flick (ms)", color=MUTED, fontsize=10)
ax.set_ylabel("angle from start (deg)", color=MUTED, fontsize=10)
ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0.01, 0.97), fontsize=10, labelcolor=MUTED, ncol=1)
fig.subplots_adjust(left=0.075, right=0.97, top=0.82, bottom=0.14)
fig.savefig("flick_1_vs_20.png", dpi=150, facecolor=SURFACE)
print("wrote flick_1_vs_20.png")
