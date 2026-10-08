#!/usr/bin/env python3
"""Bounded source discovery and selected YouTube audio intake."""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,re,shutil,subprocess,time

def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def run(args,timeout=90):return subprocess.run(args,check=True,capture_output=True,text=True,timeout=timeout)
def main():
 p=argparse.ArgumentParser();subs=p.add_subparsers(dest='mode',required=True)
 a=subs.add_parser('discover');a.add_argument('--queries',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--yt-dlp',default='yt-dlp');a.add_argument('--workers',type=int,default=3)
 a=subs.add_parser('download');a.add_argument('--catalog',type=Path,required=True);a.add_argument('--root',type=Path,required=True);a.add_argument('--yt-dlp',default='yt-dlp');a.add_argument('--workers',type=int,default=3)
 args=p.parse_args()
 if args.mode=='discover':
  queries=json.loads(args.queries.read_text());results={}
  def one(q):
   try:
    r=run([args.yt_dlp,'--flat-playlist','--dump-single-json','--no-warnings','ytsearch3:'+q['query']],60)
    d=json.loads(r.stdout);es=[{k:e.get(k) for k in ['id','title','channel','uploader','duration','url','channel_id']} for e in d['entries']]
    return q['id'],{'query':q['query'],'candidates':es}
   except Exception as e:return q['id'],{'query':q['query'],'error':str(e)}
  with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
   for k,v in pool.map(one,queries):results[k]=v;write(args.output,results);print(k,json.dumps(v,ensure_ascii=False),flush=True)
 else:
  root=args.root.resolve();catalog=json.loads(args.catalog.read_text());tracks=catalog['tracks'];ids=[t['id'] for t in tracks]
  assert len(set(ids))==len(ids)
  assert len(set(t['url'] for t in tracks))==len(tracks),'Duplicate selected URLs'
  for t in tracks:
   assert re.fullmatch('[a-z0-9][a-z0-9-]{0,63}',t['id'])
   assert re.fullmatch(r'https://(?:www\.)?youtube\.com/watch\?v=[A-Za-z0-9_-]{11}',t['url'])
  def one(t):
   out=root/'sources'/t['id'];out.mkdir(parents=True,exist_ok=True);meta=out/'source.info.json';wav=out/'source.wav'
   try:
    needs_download=not meta.exists()
    if meta.exists():
     old=json.loads(meta.read_text());needs_download=old['id']!=t['url'].split('v=')[1] or not (out/f"source.{old['ext']}").is_file()
    if needs_download:
     r=run([args.yt_dlp,'--no-playlist','--no-progress','--no-warnings','--force-overwrites','--write-info-json','-f',t.get('format','bestaudio/best'),'-o',str(out/'source.%(ext)s'),t['url']],150);(out/'download.log').write_text(r.stdout+r.stderr)
    d=json.loads(meta.read_text());ext=d['ext'];delivery=out/f'source.{ext}'
    assert delivery.is_file(),f'Missing delivery {delivery}'
    needs_decode=needs_download or not wav.exists()
    if wav.exists() and not needs_decode:
     probe=json.loads(run(['ffprobe','-v','error','-select_streams','a:0','-show_entries','stream=codec_name,sample_rate,channels','-of','json',str(wav)],20).stdout)['streams'][0]
     needs_decode=probe.get('codec_name')!='pcm_f32le' or probe.get('sample_rate')!='44100' or probe.get('channels')!=2
    if needs_decode:run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-i',str(delivery),'-vn','-ar','44100','-ac','2','-c:a','pcm_f32le',str(wav)],60)
    prov={k:d.get(k) for k in ['id','title','channel','channel_id','uploader','webpage_url','duration','upload_date','ext','format_id','acodec','asr']};prov.update({'delivery_sha256':digest(delivery),'wav_sha256':digest(wav),'working_decode':'stereo float WAV, no decode-stage integer clipping','download_date_local':time.strftime('%Y-%m-%d'),'selection':t})
    write(out/'provenance.json',prov);return t['id'],{'status':'downloaded','title':d['title'],'channel':d.get('channel'),'duration':d['duration'],'file':str(wav.relative_to(root))}
   except Exception as e:
    detail=e.stderr[-4000:] if isinstance(e,subprocess.CalledProcessError) and e.stderr else str(e)
    (out/'error.log').write_text(detail)
    return t['id'],{'status':'failed','error':str(e),'detail':detail}
  receipt={}
  with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
   for k,v in pool.map(one,tracks):receipt[k]=v;write(root/'intake-receipt.json',receipt);print(k,json.dumps(v,ensure_ascii=False),flush=True)
  if any(v['status']!='downloaded' for v in receipt.values()):raise SystemExit('Some selected sources failed; inspect receipt before planning')
if __name__=='__main__':main()
