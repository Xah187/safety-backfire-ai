from pathlib import Path
import urllib.request, zipfile, json, shutil
ROOT=Path(__file__).resolve().parent; RAW=ROOT/'dataset/raw'; YOLO=ROOT/'dataset/yolo'
URLS={'train':'https://huggingface.co/datasets/keremberke/forklift-object-detection/resolve/main/data/train.zip','valid':'https://huggingface.co/datasets/keremberke/forklift-object-detection/resolve/main/data/valid.zip','test':'https://huggingface.co/datasets/keremberke/forklift-object-detection/resolve/main/data/test.zip'}
NAMES={'forklift':0,'person':1}

def prep(split,url):
    RAW.mkdir(parents=True,exist_ok=True); zp=RAW/f'{split}.zip'; out=RAW/split
    if not zp.exists(): print('Downloading',split); urllib.request.urlretrieve(url,zp)
    if not out.exists(): out.mkdir(); zipfile.ZipFile(zp).extractall(out)
    anns=list(out.rglob('*.json'))
    if not anns: raise FileNotFoundError(f'No JSON annotations in {out}')
    data=json.loads(anns[0].read_text()); cats={c['id']:c['name'].lower() for c in data['categories']}; imgs={i['id']:i for i in data['images']}; grouped={}
    for a in data['annotations']: grouped.setdefault(a['image_id'],[]).append(a)
    io=YOLO/'images'/split; lo=YOLO/'labels'/split; io.mkdir(parents=True,exist_ok=True); lo.mkdir(parents=True,exist_ok=True)
    for iid,img in imgs.items():
        matches=list(out.rglob(img['file_name']));
        if not matches: continue
        src=matches[0]; shutil.copy2(src,io/src.name); lines=[]; W,H=img['width'],img['height']
        for a in grouped.get(iid,[]):
            c=cats.get(a['category_id'],'')
            if c not in NAMES: continue
            x,y,w,h=a['bbox']; vals=((x+w/2)/W,(y+h/2)/H,w/W,h/H)
            if all(0<=v<=1 for v in vals) and vals[2]>0 and vals[3]>0: lines.append(f"{NAMES[c]} "+' '.join(f'{v:.6f}' for v in vals))
        (lo/f'{src.stem}.txt').write_text('\n'.join(lines))
for s,u in URLS.items(): prep(s,u)
(YOLO/'data.yaml').write_text(f"path: {YOLO.resolve()}\ntrain: images/train\nval: images/valid\ntest: images/test\n\nnames:\n  0: forklift\n  1: person\n")
print('Prepared:',YOLO/'data.yaml')
