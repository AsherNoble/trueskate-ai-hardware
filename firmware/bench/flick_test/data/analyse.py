import sys, csv, math

def load(path):
    rows=[]
    for line in open(path, errors="replace"):
        line=line.strip()
        if not line or line.startswith("#") or line[0].isalpha(): continue
        p=line.split(",")
        if len(p)!=7: continue
        try:
            rows.append((float(p[0]),int(p[1]),int(p[2]),float(p[3]),float(p[4]),float(p[5]),float(p[6])))
        except ValueError: continue
    return rows

def seg_metrics(rows, vlim, label):
    # rows: t,phase,flick,target,angle,vel,uq  -- one contiguous segment
    if len(rows)<5: return None
    t0=rows[0][0]; start=rows[0][4]; tgt=rows[-1][3]
    span=tgt-start
    if abs(span)<1e-6: return None
    def frac(f):
        want=start+span*f
        for r in rows:
            if (span>0 and r[4]>=want) or (span<0 and r[4]<=want):
                return r[0]-t0
        return None
    t10,t90=frac(.10),frac(.90)
    rise=(t90-t10) if (t10 is not None and t90 is not None) else None
    # overshoot
    ext=max(r[4] for r in rows) if span>0 else min(r[4] for r in rows)
    over=(ext-tgt)/span*100 if span>0 else (tgt-ext)/abs(span)*100
    over=max(0.0,over)
    # settling: last time |err|>1 deg
    band=1.0; settle=None
    for r in rows:
        if abs(r[4]-tgt)>band: settle=r[0]-t0
    # uq saturation
    sat=sum(1 for r in rows if abs(r[6])>=vlim*0.98)/len(rows)*100
    peak_uq=max(abs(r[6]) for r in rows)
    peak_vel=max(abs(r[5]) for r in rows)
    return dict(label=label, span=span, rise=rise, over=over, settle=settle,
                sat=sat, peak_uq=peak_uq, peak_vel=peak_vel,
                dur=rows[-1][0]-t0, final=rows[-1][4], tgt=tgt)

def split_phases(rows):
    out=[]; cur=None
    for r in rows:
        key=(r[1],r[2])
        if cur is None or key!=cur[0]:
            cur=(key,[r]); out.append(cur)
        else: cur[1].append(r)
    return out

path=sys.argv[1]; vlim=float(sys.argv[2])
rows=load(path)
print(f"{path}: {len(rows)} samples, {rows[-1][0]:.0f} ms")
names={0:"idle",1:"out",2:"back",3:"dwell"}
res=[]
for (ph,fl),seg in split_phases(rows):
    if ph in (1,2):
        m=seg_metrics(seg,vlim,f"{names[ph]}{'' if fl==0 else ' #'+str(fl)}")
        if m: res.append(m)
hdr=f"{'segment':<12}{'span':>8}{'rise':>8}{'over%':>8}{'settle':>8}{'satUq%':>8}{'pkUq':>7}{'pkVel':>8}{'dur':>7}"
print(hdr); print("-"*len(hdr))
for m in res:
    r=f"{m['rise']:.0f}" if m['rise'] is not None else "-"
    s=f"{m['settle']:.0f}" if m['settle'] is not None else "0"
    print(f"{m['label']:<12}{m['span']:>8.1f}{r:>8}{m['over']:>8.1f}{s:>8}{m['sat']:>8.1f}{m['peak_uq']:>7.2f}{m['peak_vel']:>8.0f}{m['dur']:>7.0f}")
