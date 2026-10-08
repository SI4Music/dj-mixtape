#!/usr/bin/env python3
"""Check real audio and source timeline; prepare full streaming delivery."""
from pathlib import Path
import argparse,hashlib,json,math,re,subprocess,shutil
import numpy as np,soundfile as sf
from render import measure,digest

def stamp(t):
 t=max(0,int(t));return f'{t//3600:02}:{t%3600//60:02}:{t%60:02}'
def main():
 p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--root',type=Path,required=True);a=p.parse_args();root=a.root.resolve();plan=json.loads(a.plan.read_text());out=root/'output';mix=out/'mix.wav';info=sf.info(mix);assert info.channels==2 and info.samplerate==plan['sample_rate'];assert abs(info.duration-plan['duration'])<=1/info.samplerate
 peak=0.;square=0.;silent=[];rms_bins=[];pos=0
 with sf.SoundFile(mix) as h:
  for b in h.blocks(blocksize=info.samplerate,dtype='float64',always_2d=True):
   assert np.isfinite(b).all();peak=max(peak,float(np.max(np.abs(b))));square+=float(np.sum(b*b));rms=float(np.sqrt(np.mean(b*b)));rms_bins.append(rms)
   if rms<10**(-65/20):silent.append(pos)
   pos+=len(b)/info.samplerate
 assert peak<.9999,'Sample clipping'
 unexpected=[t for t in silent if 2<t<plan['duration']-3];assert not unexpected,f'Unexplained silence seconds: {unexpected}'
 loud=measure(mix);assert loud['input_tp']<=-1,'True peak ceiling exceeded'
 layers=json.loads((root/'layers.json').read_text());gain=10**(plan['master_gain_db']/20);errors=[];windows=[]
 with sf.SoundFile(mix) as h:
  for tr in plan['transitions']:
   center=tr['end'];start=max(0,center-3);length=min(8,plan['duration']-start);frame=round(start*info.samplerate);count=round(length*info.samplerate);h.seek(frame);actual=h.read(count,always_2d=True);expect=np.zeros_like(actual)
   for l in layers:
    f=root/l['file'];fi=sf.info(f);lp=round(l['position']*info.samplerate);lo=max(frame,lp);hi=min(frame+len(actual),lp+fi.frames)
    if hi>lo:
     y,_=sf.read(f,start=lo-lp,frames=hi-lo,always_2d=True);expect[lo-frame:hi-frame]+=y*gain
   err=float(np.max(np.abs(expect-actual)));assert err<3e-7;errors.append(err)
   windows.append({'from':tr['from'],'to':tr['to'],'type':tr['type'],'mix_start':tr['start'],'mix_end':tr['end'],'pcm_sum_max_error':err,'sample_peak_dbfs':float(20*np.log10(np.max(np.abs(actual))+1e-15))})
 # Validate exported RPP file references and item placements against layer metadata.
 text=(out/'mixtape.rpp').read_text();paths=re.findall(r'^\s+FILE "([^"]+)"',text,re.M);assert len(paths)==len(layers)
 for path in paths:assert (out/path).resolve().is_file(),path
 positions=[float(v) for v in re.findall(r'^\s+POSITION ([0-9.]+)$',text,re.M)];assert len(positions)==len(layers)
 assert all(abs(x-l['position'])<1e-7 for x,l in zip(positions,layers))
 listen=root/'listen';listen.mkdir(exist_ok=True);mp3=listen/'mix.mp3'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-i',str(mix),'-c:a','libmp3lame','-b:a','256k',str(mp3)],check=True)
 mloud=measure(mp3);assert mloud['input_tp']<0
 transcript=['# Vietnamese hiphop trap drill DJ mix','',f"Thời lượng {stamp(info.duration)}. Render bằng FFmpeg trên máy. Các cue và chuyển tiếp là bản thử từ phân tích; chưa có kiểm định nghe bởi người.",'','| Vào mix | Nghệ sĩ | Bài | BPM nguồn dự đoán | Rate | Đoạn nguồn | Chuyển vào |','|---|---|---|---:|---:|---|---|'];tracks=[]
 for i,s in enumerate(plan['segments']):
  t={'index':i+1,'id':s['id'],'artist':s['artist'],'title':s['title'],'start':s['position'],'end':s['position']+s['source_length']/s['playrate'],'url':s['url'],'bpm':s.get('bpm'),'transition_in':'opening' if i==0 else plan['transitions'][i-1]['type']};tracks.append(t)
  transcript.append(f"| {stamp(t['start'])} | {s['artist']} | [{s['title']}]({s['url']}) | {s.get('bpm','')} | {s['playrate']:.4f} | {s['source_start']:.2f}–{s['source_start']+s['source_length']:.2f} s | {t['transition_in']} |")
 (root/'TRACKLIST.md').write_text('\n'.join(transcript)+'\n');(listen/'set.json').write_text(json.dumps({'title':plan['title'],'duration':info.duration,'tracks':tracks,'rms_step':1,'rms':rms_bins,'disclosure':'DJ edit từ audio gốc YouTube. Cue/grid được dự đoán; chưa kiểm định nghe bằng người. Rate, gain, fade, filter và echo đã bake vào từng clip; vị trí và mức track chỉnh được trong project.'},ensure_ascii=False,separators=(',',':')))
 asset=Path(__file__).resolve().parents[1]/'assets/player'
 for f in asset.iterdir():
  if f.is_file():shutil.copy2(f,listen/f.name)
 receipt={'status':'technical_pass','duration':info.duration,'frames':info.frames,'sample_rate':info.samplerate,'channels':info.channels,'sample_peak_dbfs':20*math.log10(peak),'rms_dbfs':10*math.log10(square/(info.frames*2)),'wav_loudness':loud,'mp3_loudness':mloud,'unexplained_silent_seconds':unexpected,'transitions':windows,'max_transition_sum_error':max(errors,default=0),'resolved_project_media_files':len(paths),'reaper_opened':False,'human_listening_review':None,'plan_sha256':digest(a.plan),'mix_sha256':digest(mix),'project_sha256':digest(out/'mixtape.rpp'),'mp3_sha256':digest(mp3),'script_sha256':digest(Path(__file__))}
 (root/'verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2));print(json.dumps({k:receipt[k] for k in ['status','duration','sample_peak_dbfs','wav_loudness','mp3_loudness','resolved_project_media_files','max_transition_sum_error']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
