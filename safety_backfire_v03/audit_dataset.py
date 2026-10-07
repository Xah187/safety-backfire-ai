from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parent/'dataset/yolo'
for s in ['train','valid','test']:
    labels=list((R/'labels'/s).glob('*.txt')); images=list((R/'images'/s).iterdir()); c=Counter(); empty=bad=0
    for f in labels:
        t=f.read_text().strip()
        if not t: empty+=1; continue
        for line in t.splitlines():
            p=line.split()
            if len(p)!=5: bad+=1; continue
            c[int(p[0])]+=1
            if not all(0<=float(x)<=1 for x in p[1:]): bad+=1
    print(s, 'images=',len(images),'labels=',len(labels),'classes=',dict(c),'empty=',empty,'invalid=',bad)
