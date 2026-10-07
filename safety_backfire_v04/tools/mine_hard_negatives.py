from pathlib import Path
import argparse, csv, cv2
from ultralytics import YOLO

def main():
    p=argparse.ArgumentParser(description='Mine V0.3 predictions for manual hard-negative review.')
    p.add_argument('--model', required=True)
    p.add_argument('--input', required=True)
    p.add_argument('--output', default='data/hard_negatives')
    p.add_argument('--forklift-conf', type=float, default=0.30)
    p.add_argument('--person-conf', type=float, default=0.30)
    p.add_argument('--imgsz', type=int, default=960)
    p.add_argument('--device', default='mps')
    args=p.parse_args()
    out=Path(args.output); out.mkdir(parents=True, exist_ok=True)
    model=YOLO(args.model)
    cap=cv2.VideoCapture(str(args.input)); fps=cap.get(cv2.CAP_PROP_FPS) or 30
    csv_path=out/'predictions.csv'
    with csv_path.open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['frame','time_sec','forklift_count','max_forklift_conf','person_count','max_person_conf','image'])
        idx=0
        while True:
            ok,frame=cap.read()
            if not ok: break
            # V0.3 class order: 0=forklift, 1=person
            r=model.predict(frame, imgsz=args.imgsz, conf=min(args.forklift_conf,args.person_conf), device=args.device, verbose=False)[0]
            fc=[]; pc=[]
            if r.boxes is not None:
                for b in r.boxes:
                    c=int(b.cls.item()); conf=float(b.conf.item())
                    if c==0 and conf>=args.forklift_conf: fc.append(conf)
                    if c==1 and conf>=args.person_conf: pc.append(conf)
            if fc:
                name=f'frame_{idx:06d}_forklift_pred.jpg'; cv2.imwrite(str(out/name),frame)
                w.writerow([idx,round(idx/fps,3),len(fc),round(max(fc),4),len(pc),round(max(pc),4) if pc else 0,name])
            idx+=1
    cap.release(); print('Saved:',csv_path)
    print('Review every saved image. False forklift predictions are hard negatives; true objects must be annotated, not treated as background.')
if __name__=='__main__': main()
