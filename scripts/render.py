#!/usr/bin/env python3
"""Native FFmpeg DJ mix renderer with individual processed media and RPP timeline."""
from pathlib import Path
import argparse,hashlib,json,math,re,shutil,subprocess,time,uuid
import numpy as np,soundfile as sf

def run(cmd,timeout=240):
 r=subprocess.run(cmd,check=True,capture_output=True,text=True,timeout=timeout);return r
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def measure(path):
 r=run(['ffmpeg','-hide_banner','-nostdin','-i',str(path),'-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-'])
 d=json.loads(re.findall(r'\{[^{}]*"input_i"[^{}]*\}',r.stderr)[-1]);return {k:float(d[k]) for k in ['input_i','input_tp','input_lra']}
def quote(s):return '"'+str(s).replace('\\','/').replace('"',"'").replace('\n',' ')+'"'
def number(x):return f'{float(x):.9f}'
def write_rpp(root,plan,layers,master_gain):
 out=root/'output';rows=['<REAPER_PROJECT 0.1 "7.82" 0','  SAMPLERATE '+str(plan['sample_rate'])+' 0 0','  TEMPO 140 4 4','  MASTERVOLPAN '+number(master_gain)+' 0 -1 -1 1','  RENDER_FILE '+quote('mix.wav'),'  RENDER_FMT 0 2 '+str(plan['sample_rate']),'  RENDER_RANGE 0 0 '+number(plan['duration'])+' 0 1000']
 for i,s in enumerate(plan['segments']):
  rows.append('  MARKER '+str(i+1)+' '+number(s['position'])+' '+quote(f"{i+1:02} {s['artist']} — {s['title']}")+' 0')
 for layer in layers:
  f=root/layer['file'];dur=sf.info(f).duration;rel='../'+layer['file'];name=layer['name']
  rows.extend(['  <TRACK {'+str(uuid.uuid4()).upper()+'}','    NAME '+quote(name),'    VOLPAN 1 0 1 -1','    MAINSEND 1','    <ITEM','      POSITION '+number(layer['position']),'      SNAPOFFS 0','      LENGTH '+number(dur),'      VOLPAN 1 0 1 -1','      SOFFS 0','      FADEIN 1 0 0','      FADEOUT 1 0 0','      NAME '+quote(f.name),'      <SOURCE WAVE','        FILE '+quote(rel),'      >','    >','  >'])
 rows.append('>');p=out/'mixtape.rpp';p.write_text('\n'.join(rows)+'\n');return p
def main():
 p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--root',type=Path,required=True);a=p.parse_args();root=a.root.resolve();plan=json.loads(a.plan.read_text());sr=plan['sample_rate'];duration=plan['duration'];segments=plan['segments'];assert duration>0 and sr in [44100,48000]
 media=root/'media';out=root/'output';media.mkdir(exist_ok=True);out.mkdir(exist_ok=True);layers=[];receipt={'render_engine':'native FFmpeg','reaper_rendered':False,'plan_sha256':digest(a.plan),'segments':{},'created_unix':time.time()}
 for i,s in enumerate(segments):
  assert 0<=s['source_start'] and 0<s['source_length'] and .5<=s['playrate']<=2
  assert s['position']>=0 and s['position']+s['source_length']/s['playrate']<=duration+.01
  source=root/s['file'];target=media/f"{i+1:02}-{s['id']}.wav";length=s['source_length']/s['playrate'];raw=media/f"{i+1:02}-{s['id']}-unfaded.wav"
  base=[f"atempo={s['playrate']:.9f}"]
  if s.get('normalization')=='dynamic_loudnorm':base.extend([f"loudnorm=I={plan.get('clip_target_lufs',-16)}:TP=-2:LRA=11",f'aresample={sr}'])
  # End by sample index: normalization can shift timestamps; duration trim may lose samples.
  selected_frames=round(length*sr)
  base.extend([f'apad=whole_len={selected_frames}',f'atrim=end_sample={selected_frames}'])
  run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-ss',number(s['source_start']),'-t',number(s['source_length']),'-i',str(source),'-af',','.join(base),'-ar',str(sr),'-ac','2','-c:a','pcm_f32le',str(raw)])
  loud=measure(raw);gain=min(plan.get('clip_target_lufs',-16)-loud['input_i'],-2-loud['input_tp']);s['gain_db']=round(gain,6)
  fades=[f'volume={gain:.9f}dB']
  if s['fade_in']>0:fades.append(f"afade=t=in:st=0:d={s['fade_in']:.9f}:curve=qsin")
  if s['fade_out']>0:fades.append(f"afade=t=out:st={max(0,length-s['fade_out']):.9f}:d={s['fade_out']:.9f}:curve=qsin")
  y,rs=sf.read(raw,always_2d=True)
  # Filter only the exit region, with a gradual dry/highpassed crossfade.
  tail=s.get('filter_out',0)
  if tail>0:
   from scipy.signal import butter,sosfilt
   n=min(len(y),round(tail*sr));filtered=sosfilt(butter(2,280,fs=sr,btype='highpass',output='sos'),y[-n:],axis=0);ramp=np.linspace(0,1,n)[:,None];y[-n:]=y[-n:]*(1-ramp)+filtered*ramp
   sf.write(raw,y,sr,subtype='FLOAT')
  run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-i',str(raw),'-af',','.join(fades),'-c:a','pcm_f32le',str(target)])
  assert sf.info(target).frames==selected_frames, 'Prepared recording differs from selected frame count'
  layers.append({'name':f"{i+1:02} {s['artist']} — {s['title']}",'id':s['id'],'file':str(target.relative_to(root)),'position':s['position'],'kind':'recording'})
  if s.get('echo'):
   e=s['echo'];et=media/f"{i+1:02}-{s['id']}-echo.wav";st=max(0,e['source_offset']);nl=round(e['source_length']*sr);src=y[round(st*sr):round(st*sr)+nl]*10**(gain/20);delay=round(e['delay']*sr);count=5;echo=np.zeros((len(src)+delay*count,2))
   for k in range(1,count+1):echo[delay*k:delay*k+len(src)]+=src*(e['decay']**(k-1))*10**(e['gain_db']/20)
   from scipy.signal import butter,sosfilt
   echo=sosfilt(butter(2,[450,4800],btype='bandpass',fs=sr,output='sos'),echo,axis=0);fade=min(round(.04*sr),len(echo));echo[:fade]*=np.linspace(0,1,fade)[:,None];echo[-fade:]*=np.linspace(1,0,fade)[:,None]
   remaining=round((duration-e['position'])*sr);echo=echo[:remaining];sf.write(et,echo,sr,subtype='FLOAT');layers.append({'name':f"FX echo {s['id']}",'id':s['id']+'-echo','file':str(et.relative_to(root)),'position':e['position'],'kind':'echo'})
  raw.unlink();receipt['segments'][s['id']]={'source_sha256':digest(source),'prepared_sha256':digest(target),'prepared_frames':sf.info(target).frames,'excerpt_loudness_before_gain':loud,'normalization':s.get('normalization','uniform_gain'),'gain_db':gain,'playrate':s['playrate'],'position':s['position']};print('Prepared',s['id'],round(gain,2),'dB',flush=True)
 for i,b in enumerate(plan.get('bridges',[])):
  source=root/b['file'];wave,bsr=sf.read(source,start=round(b.get('source_start',0)*sr),frames=round(b['source_length']*sr),always_2d=True);assert bsr==sr
  loop=np.tile(wave,(b['repeats'],1))*10**(b['gain_db']/20)
  from scipy.signal import butter,sosfilt
  loop=sosfilt(butter(2,b.get('highpass_hz',150),fs=sr,btype='highpass',output='sos'),loop,axis=0)
  fi=min(round(b.get('fade_in',.03)*sr),len(loop));fo=min(round(b.get('fade_out',.12)*sr),len(loop));loop[:fi]*=np.linspace(0,1,fi)[:,None];loop[-fo:]*=np.linspace(1,0,fo)[:,None]
  path=media/f"bridge-{i+1:02}.wav";sf.write(path,loop,sr,subtype='FLOAT');assert b['position']+len(loop)/sr<=duration+.01
  layers.append({'name':b['name'],'id':f'bridge-{i+1:02}','file':str(path.relative_to(root)),'position':b['position'],'kind':'loop-bridge'})
 # Blockwise deterministic sum, rather than hour-long arrays per recording.
 premaster=out/'premaster.wav';frames=round(duration*sr);handles=[(sf.SoundFile(root/l['file']),round(l['position']*sr)) for l in layers];block=sr*5
 with sf.SoundFile(premaster,'w',samplerate=sr,channels=2,subtype='FLOAT') as dest:
  for pos in range(0,frames,block):
   count=min(block,frames-pos);mix=np.zeros((count,2),dtype=np.float64)
   for h,start in handles:
    left=max(pos,start);right=min(pos+count,start+len(h))
    if right>left:h.seek(left-start);mix[left-pos:right-pos]+=h.read(right-left,dtype='float64',always_2d=True)
   dest.write(mix)
 for h,_ in handles:h.close()
 loud=measure(premaster);master=min(plan.get('master_target_lufs',-14)-loud['input_i'],-1.5-loud['input_tp']);plan['master_gain_db']=round(master,6)
 rendered=out/'mix.wav';run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-i',str(premaster),'-af',f'volume={master:.9f}dB','-c:a','pcm_s24le',str(rendered)],240)
 project=write_rpp(root,plan,layers,10**(master/20));(root/'layers.json').write_text(json.dumps(layers,ensure_ascii=False,indent=2));a.plan.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');receipt.update({'final_plan_sha256':digest(a.plan),'premaster_loudness':loud,'master_gain_db':master,'mix_sha256':digest(rendered),'project_sha256':digest(project),'baked_processing':['selected source cut','pitch-preserving atempo','clip gain','fades','exit highpass','echo'],'editable_in_project':['individual item positions','item boundaries','per-track gain','effect-layer positions','master gain'],'script_sha256':digest(Path(__file__))});(root/'render-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2));print('Rendered',duration,'seconds',master,'dB master',flush=True)
if __name__=='__main__':main()
