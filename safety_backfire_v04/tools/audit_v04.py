from pathlib import Path
import argparse, collections

def audit(root):
    root=Path(root); imgs=root/'images'; labels=root/'labels'; exts={'.jpg','.jpeg','.png','.webp'}
    counts=collections.Counter(); empty=0; bad=0; nimg=0
    for ip in imgs.rglob('*'):
        if ip.suffix.lower() not in exts: continue
        nimg+=1; lp=labels/ip.relative_to(imgs); lp=lp.with_suffix('.txt')
        if not lp.exists(): bad+=1; continue
        text=lp.read_text().strip()
        if not text: empty+=1; continue
        for line in text.splitlines():
            parts=line.split()
            if len(parts)!=5: bad+=1; continue
            try:
                c=int(parts[0]); vals=list(map(float,parts[1:]));
                if c not in (0,1) or any(v<0 or v>1 for v in vals) or vals[2]<=0 or vals[3]<=0: bad+=1
                else: counts[c]+=1
            except: bad+=1
    print(f'{root}: images={nimg}, empty_labels={empty}, bad_records={bad}, forklift_boxes={counts[0]}, person_boxes={counts[1]}')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--root',default='data/stress_train'); args=p.parse_args(); audit(args.root)
if __name__=='__main__': main()
