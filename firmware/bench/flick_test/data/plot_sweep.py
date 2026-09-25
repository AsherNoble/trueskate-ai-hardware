import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE="#fcfcfb"; INK="#1a1a19"; MUTED="#6b6b68"; GRID="#e6e6e3"
CMD="#2a78d6"; MEAS="#eb6834"
SERIES=["#2a78d6","#eb6834","#1baf7a","#eda100"]

def load(path):
    t=[];tg=[];an=[];uq=[];ph=[]
    for line in open(path,errors="replace"):
        line=line.strip()
        if not line or line.startswith("#") or line[0].isalpha(): continue
        p=line.split(",")
        if len(p)!=7: continue
        try:
            t.append(float(p[0])/1000);tg.append(float(p[3]))
            an.append(float(p[4]));uq.append(float(p[6]));ph.append(int(p[1]))
        except ValueError: pass
    return t,tg,an,uq,ph

def style(ax):
    ax.set_facecolor(SURFACE); ax.grid(True,color=GRID,linewidth=.8,zorder=0)
    ax.set_axisbelow(True)
    for s in ("top","right"): ax.spines[s].set_visible(False)
    for s in ("left","bottom"): ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED,labelsize=9)

def single(path,out,title,sub,vlim):
    t,tg,an,uq,_=load(path)
    fig,(ax,ax2)=plt.subplots(2,1,figsize=(11,6.2),sharex=True,
        gridspec_kw=dict(height_ratios=[3,1],hspace=.12))
    fig.patch.set_facecolor(SURFACE)
    ax.plot(t,tg,color=CMD,linewidth=2.0,label="commanded",zorder=3)
    ax.plot(t,an,color=MEAS,linewidth=2.0,label="measured",zorder=4)
    style(ax); ax.set_ylabel("angle (deg)",color=MUTED,fontsize=10)
    ax.set_title(title,color=INK,fontsize=14,weight="bold",loc="left",pad=14)
    ax.text(0,1.015,sub,transform=ax.transAxes,color=MUTED,fontsize=10,va="bottom")
    ax.legend(frameon=False,loc="upper right",fontsize=10,labelcolor=MUTED,ncol=2)
    ax2.plot(t,uq,color=MUTED,linewidth=1.5,zorder=3)
    for s in (1,-1): ax2.axhline(s*vlim,color="#d03b3b",linewidth=1.2,linestyle="--",zorder=2)
    ax2.text(t[-1],vlim,f" limit {vlim:g} V",color="#d03b3b",fontsize=9,va="center",clip_on=False)
    style(ax2); ax2.set_ylabel("Uq (V)",color=MUTED,fontsize=10)
    ax2.set_xlabel("time (s)",color=MUTED,fontsize=10); ax2.set_ylim(-vlim*1.45,vlim*1.45)
    fig.subplots_adjust(left=.075,right=.90,top=.86,bottom=.10)
    fig.savefig(out,dpi=150,facecolor=SURFACE); plt.close(fig); print("wrote",out)

runs=[("flick_p40_2v.csv","P_angle 40, 2 V","full cycle 225 ms · Uq saturated 12.8%",2.0),
      ("flick_p40_4v.csv","P_angle 40, 4 V","full cycle 219 ms · Uq saturated 6.3%",4.0),
      ("flick_p80_4v.csv","P_angle 80, 4 V","full cycle 147 ms · Uq saturated 18.8%",4.0),
      ("flick_p80_6v.csv","P_angle 80, 6 V","full cycle 233 ms · Uq saturated 8.9% · overshoot 3.7%",6.0),
      ("flick_p160_2v.csv","P_angle 160, 2 V","full cycle 118 ms · Uq saturated 63.3%",2.0),
      ("flick_p160_4v.csv","P_angle 160, 4 V","full cycle 90 ms · Uq saturated 43.5% · FASTEST CLEAN",4.0),
      ("flick_p160_6v.csv","P_angle 160, 6 V","full cycle 94 ms · Uq saturated 34.4% · overshoot 3.9%",6.0)]
for f,title,sub,v in runs:
    single(f,f.replace(".csv",".png"),"Flick — "+title,"axis 1, 60° out and straight back · "+sub,v)

# ---- overlay: best run per P_angle, aligned on stroke start --------------
ov=[("flick_2v.csv","P_angle 20 · 2 V · 417 ms"),
    ("flick_p40_4v.csv","P_angle 40 · 4 V · 219 ms"),
    ("flick_p80_4v.csv","P_angle 80 · 4 V · 147 ms"),
    ("flick_p160_4v.csv","P_angle 160 · 4 V · 90 ms")]
fig,ax=plt.subplots(figsize=(11,5.6)); fig.patch.set_facecolor(SURFACE)
for i,(f,lab) in enumerate(ov):
    t,tg,an,uq,ph=load(f)
    idx=[k for k in range(len(ph)) if ph[k] in (1,2)]
    if not idx: continue
    k0=idx[0]; base=an[k0]; t0=t[k0]
    xs=[(t[k]-t0)*1000 for k in idx]; ys=[an[k]-base for k in idx]
    ax.plot(xs,ys,color=SERIES[i],linewidth=2.0,zorder=3+i,label=lab)
    # Direct-label at each curve's peak: the ends all converge on zero and
    # would overprint each other and the legend.
    pk=max(range(len(ys)),key=lambda k:ys[k])
    ax.text(xs[pk],ys[pk]+2.5+(4.5 if i%2 else 0),lab.split(" · ")[0],color=SERIES[i],
            fontsize=9.5,ha="center",va="bottom",weight="bold",zorder=8)
ax.axhline(60,color=MUTED,linewidth=1.2,linestyle="--",zorder=2)
ax.text(515,61.2,"commanded 60°",color=MUTED,fontsize=9,va="bottom",ha="right")
style(ax)
ax.set_title("Flick response across the P_angle sweep",color=INK,fontsize=14,
             weight="bold",loc="left",pad=26)
ax.text(0,1.02,"each gain at its fastest clean voltage · aligned on stroke start · motor unloaded",
        transform=ax.transAxes,color=MUTED,fontsize=10,va="bottom")
ax.set_xlabel("time from stroke start (ms)",color=MUTED,fontsize=10)
ax.set_ylabel("angle from start (deg)",color=MUTED,fontsize=10)
ax.set_xlim(-10,520); ax.set_ylim(-6,72)
ax.legend(frameon=False,loc="lower right",fontsize=10,labelcolor=MUTED)
fig.subplots_adjust(left=.075,right=.88,top=.85,bottom=.13)
fig.savefig("sweep_overlay.png",dpi=150,facecolor=SURFACE)
print("wrote sweep_overlay.png")
