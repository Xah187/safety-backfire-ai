from pathlib import Path
import argparse, shutil, random, yaml

def copy_split(src_img,src_lbl,dst_img,dst_lbl,prefix):
    n=0
    for ip in sorted(Path(src_img).glob('*')):
        if ip.suffix.lower() not in {'.jpg','.jpeg','.png','.webp'}: continue
        lp=Path(src_lbl)/(ip.stem+'.txt')
        if not lp.exists(): continue
        name=f'{prefix}_{ip.name}'
        shutil.copy2(ip,Path(dst_img)/name)
        shutil.copy2(lp,Path(dst_lbl)/(Path(name).stem+'.txt'))
        n+=1
    return n

def main():
    p=argparse.ArgumentParser(); p.add_argument('--base',required=True); p.add_argument('--stress',default='data/stress_train'); p.add_argument('--out',default='data/v04'); p.add_argument('--val-frac',type=float,default=.15); p.add_argument('--seed',type=int,default=42); args=p.parse_args()
    base=Path(args.base); stress=Path(args.stress); out=Path(args.out); random.seed(args.seed)
    for split in ['train','valid','test']:
        (out/'images'/split).mkdir(parents=True,exist_ok=True); (out/'labels'/split).mkdir(parents=True,exist_ok=True)
    for split in ['train','valid','test']:
        copy_split(base/'images'/split,base/'labels'/split,out/'images'/split,out/'labels'/split,'base')
    files=[p for p in (stress/'images').glob('*') if p.suffix.lower() in {'.jpg','.jpeg','.png','.webp'}]
    random.shuffle(files); nv=max(1,round(len(files)*args.val_frac)) if files else 0
    val=set(files[:nv]);
    for ip in files:
        lp=stress/'labels'/(ip.stem+'.txt');
        if not lp.exists(): continue
        split='valid' if ip in val else 'train'; name='cctv_'+ip.name
        shutil.copy2(ip,out/'images'/split/name); shutil.copy2(lp,out/'labels'/split/(Path(name).stem+'.txt'))
    (out/'data.yaml').write_text(yaml.safe_dump({'path':str(out.resolve()),'train':'images/train','val':'images/valid','test':'images/test','names':{0:'forklift',1:'person'}},sort_keys=False))
    print('Built:',out/'data.yaml')
if __name__=='__main__': main()
