import math
def normalize(rows,duration):
    if not isinstance(rows,list):raise ValueError('bad engine schema')
    out=[]
    for row in rows:
        a,b,n=float(row['start']),float(row['end']),int(row['speaker'])
        if not(math.isfinite(a) and math.isfinite(b) and 0<=a<b and a<duration and b<=duration+0.1 and 1<=n<=8):raise ValueError('invalid segment')
        out.append({'start':round(a,3),'end':round(min(b,duration),3),'speaker_id':f'SPEAKER_{n-1:02d}'})
    return sorted(out,key=lambda s:(s['start'],s['end'],s['speaker_id']))
