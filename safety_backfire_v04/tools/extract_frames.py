from pathlib import Path
import argparse, cv2, math

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input', required=True, help='Video file or directory of videos')
    p.add_argument('--output', default='data/extracted_frames')
    p.add_argument('--every-sec', type=float, default=1.0)
    args=p.parse_args()
    src=Path(args.input); out=Path(args.output); out.mkdir(parents=True, exist_ok=True)
    videos=[src] if src.is_file() else sorted(src.glob('**/*'))
    videos=[v for v in videos if v.suffix.lower() in {'.mp4','.mov','.avi','.mkv','.m4v'}]
    total=0
    for vp in videos:
        cap=cv2.VideoCapture(str(vp)); fps=cap.get(cv2.CAP_PROP_FPS) or 30
        step=max(1,int(round(fps*args.every_sec))); idx=0; saved=0
        stem=vp.stem.replace(' ','_')
        while True:
            ok,frame=cap.read()
            if not ok: break
            if idx % step == 0:
                path=out/f'{stem}_f{idx:06d}.jpg'
                cv2.imwrite(str(path),frame,[int(cv2.IMWRITE_JPEG_QUALITY),92]); saved+=1; total+=1
            idx+=1
        cap.release(); print(f'{vp.name}: {saved} frames')
    print(f'Total: {total}')
if __name__=='__main__': main()
