import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
SURFACE="#fcfcfb";INK="#1a1a19";MUTED="#6b6b68";GRID="#e6e6e3"
CMD="#2a78d6";MEAS="#eb6834"
def win(n):
    seg=[]
    for l in open("flick20_p160_4v.csv",errors="replace"):
        l=l.strip()
        if not l or l[0].isalpha() or l.startswith("#"): continue
        q=l.split(",")
        if len(q)!=7: continue
        if int(q[2])==n and int(q[1]) in (1,2):
            seg.append((float(q[0]),float(q[3]),float(q[4])))
    if not seg: return None
    t0=seg[0][0];b=seg[0][2]
    return [(s[0]-t0,s[1]-b,s[2]-b) for s in seg]
f1,f20=win(1),win(20)
fig,ax=plt.subplots(figsize=(11,4.8));fig.patch.set_facecolor(SURFACE)
ax.plot([p[0] for p in f1],[p[1] for p in f1],color=MUTED,linewidth=1.4,
        linestyle="--",zorder=2,label="commanded")
ax.plot([p[0] for p in f1],[p[2] for p in f1],color=CMD,linewidth=2.0,zorder=3,label="flick 1")
ax.plot([p[0] for p in f20],[p[2] for p in f20],color=MEAS,linewidth=2.0,zorder=4,label="flick 20")
ax.set_facecolor(SURFACE);ax.grid(True,color=GRID,linewidth=.8,zorder=0);ax.set_axisbelow(True)
for s in ("top","right"): ax.spines[s].set_visible(False)
for s in ("left","bottom"): ax.spines[s].set_color(GRID)
ax.tick_params(colors=MUTED,labelsize=9)
ax.set_title("Flick 1 vs flick 20 at P_angle 160 / 4 V — thermal drift check",
             color=INK,fontsize=14,weight="bold",loc="left",pad=26)
ax.text(0,1.02,"43% Uq saturation, 7.0 s of continuous duty between them",
        transform=ax.transAxes,color=MUTED,fontsize=10,va="bottom")
ax.set_xlabel("time within flick (ms)",color=MUTED,fontsize=10)
ax.set_ylabel("angle from start (deg)",color=MUTED,fontsize=10)
ax.legend(frameon=False,loc="upper right",fontsize=10,labelcolor=MUTED)
fig.subplots_adjust(left=.075,right=.97,top=.82,bottom=.15)
fig.savefig("flick_1_vs_20_p160.png",dpi=150,facecolor=SURFACE)
print("wrote flick_1_vs_20_p160.png")
