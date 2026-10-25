"""Authoritative placement transform for the 3+3 carrier, millimetres."""
WIDTH, HEIGHT = 150, 140
BANKS = {'upper': [2, 3, 5], 'lower': [1, 4, 6]}
SD_SERVICE = [61.66, 62.5, 81.66, 77.5]
def axis_point(axis, x, y):
    bank = 'upper' if axis in BANKS['upper'] else 'lower'
    offset = 8 + 35 * BANKS[bank].index(axis)
    return (offset + x, y) if bank == 'upper' else (offset + 26 - x, HEIGHT-y)
def axis_angle(axis, angle):
    return (angle + (180 if axis in BANKS['lower'] else 0)) % 360

def place(parts):
    shared = {'J1':(1.97,77.62,90), 'J2':(1.97,62.38,90),
      'J5':(145,56,90), 'F1':(135,42,90), 'J6':(147,95,0),
      'Q1':(126,24,90), 'R2':(122,32,270), 'D1':(120,9,0),
      'R1':(126,127,0), 'U1':(125,67,0), 'U2':(125,103,0),
      'C1':(125,61,0), 'C2':(125,97,0)}
    for axis in range(1,7):
        shared[f'R{40+axis}']=(139,65+13*(axis-1),270)
    local = {'J1':(21,13,270), 'J2':(6.58,3,270), 'J3':(18,3.3,180),
             'C1':(12.5,41.5,0), 'C2':(5,37,270),
             'R2':(2,36.5,270), 'R3':(25,37,270)}
    for p in parts:
        ref=p['ref']
        if ref in shared: p['pcb']=shared[ref]; continue
        axis=int(ref[-1]); key=ref[:-1]
        x,y,angle=local[key]
        p['pcb']=(*axis_point(axis,x,y),axis_angle(axis,angle))
