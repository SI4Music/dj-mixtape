#!/usr/bin/env python3
"""Measure sources and produce advisory beat/cue/key observations."""
from pathlib import Path
import argparse,json,os,subprocess,re
import numpy as np,librosa,soundfile as sf
def estimate_tempo(beats,start,end):
 """Fit a coherent pulse run; do not turn changing detector subdivisions into BPM."""
 sel=np.asarray(beats,dtype=float);sel=sel[(sel>start)&(sel<end)];diff=np.diff(sel)
 valid=diff[(diff>.24)&(diff<1.4)]
 if len(valid)<8:raise ValueError('Too few stable beat intervals')
 bins=np.round(valid/.02).astype(int);mode=np.bincount(bins).argmax()*.02
 period=float(np.median(valid[np.abs(valid-mode)<.04]));runs=[];lo=0
 for i,gap in enumerate(diff):
  count=max(1,round(gap/period));ok=count<=4 and abs(gap-count*period)<max(.045,.09*period)
  if not ok:
   if i-lo>=8:runs.append(sel[lo:i+1])
   lo=i+1
 if len(sel)-lo>=9:runs.append(sel[lo:])
 if not runs:raise ValueError('No coherent beat run; review source manually')
 run=max(runs,key=lambda x:x[-1]-x[0]);idx=np.r_[0,np.cumsum(np.round(np.diff(run)/period))];slope,anchor=np.polyfit(idx,run,1);error=run-(anchor+idx*slope)
 raw=60/float(slope);bpm=raw
 while bpm<90:bpm*=2
 while bpm>190:bpm/=2
 return {'raw_bpm':raw,'bpm':bpm,'pulse_period':float(slope),'pulse_anchor':float(anchor),'run_start':float(run[0]),'run_end':float(run[-1]),'pulse_count':len(run),'grid_error_rms_seconds':float(np.sqrt(np.mean(error*error))),'method':'dominant interval cluster + longest coherent pulse run; advisory'}
def loudness(p):
 r=subprocess.run(['ffmpeg','-hide_banner','-nostdin','-i',str(p),'-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-'],check=True,capture_output=True,text=True)
 d=json.loads(re.findall(r'\{[^{}]*"input_i"[^{}]*\}',r.stderr)[-1]);return {k:float(d[k]) for k in ['input_i','input_tp','input_lra']}
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--torch-home',type=Path);p.add_argument('--catalog',type=Path);a=p.parse_args();root=a.root.resolve();(root/'analysis').mkdir(exist_ok=True)
 if a.torch_home:os.environ['TORCH_HOME']=str(a.torch_home)
 tracker=None
 try:
  import torch
  torch.set_num_threads(4)
  from beat_this.inference import File2Beats
  tracker=File2Beats(checkpoint_path='final0',device='cpu',dbn=False)
 except ImportError:pass
 cat=json.loads((a.catalog or root/'catalog.json').read_text());summary={}
 for t in cat['tracks']:
  f=root/'sources'/t['id']/'source.wav';y,sr=librosa.load(f,sr=11025);dur=sf.info(f).duration
  rms=librosa.feature.rms(y=y,frame_length=2048,hop_length=512)[0];rt=librosa.frames_to_time(np.arange(len(rms)),sr=sr,hop_length=512)
  active=rt[rms>max(.006,np.percentile(rms,90)*.12)];start=float(active[0]) if len(active) else 0;end=float(min(dur,active[-1]+.15)) if len(active) else dur
  if tracker:beats,downs=tracker(str(f));model='Beat This final0'
  else:
   tempo,b=librosa.beat.beat_track(y=y,sr=sr,hop_length=256);beats=librosa.frames_to_time(b,sr=sr,hop_length=256);downs=beats[::4];model='librosa beat_track, downbeats assumed'
  tempo_fit=estimate_tempo(beats,max(15,start),min(end-4,dur-5));raw=tempo_fit['raw_bpm'];bpm=tempo_fit['bpm']
  chrom=librosa.feature.chroma_stft(y=y,sr=sr,n_fft=2048,hop_length=512);ch=np.mean(chrom,axis=1)
  profiles=[np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88]),np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])]
  keys=sorted([(float(np.corrcoef(ch,np.roll(pr,k))[0,1]),k,mode) for mode,pr in enumerate(profiles) for k in range(12)],reverse=True)
  names=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];score,k,mode=keys[0]
  onset=librosa.onset.onset_strength(y=y,sr=sr,hop_length=512);peaks=librosa.util.peak_pick(onset,pre_max=3,post_max=3,pre_avg=5,post_avg=5,delta=.5,wait=3)
  db=[float(x) for x in downs if start+.15<=x<end-2]
  d={'id':t['id'],'duration':dur,'sample_rate':sf.info(f).samplerate,'active_start':start,'active_end':end,'raw_bpm':raw,'bpm':round(bpm,3),'tempo_fit':tempo_fit,'beat_model':model,'beats':[float(x) for x in beats],'downbeats':[float(x) for x in downs],'cue_candidates':db,'key_estimate':names[k]+(' minor' if mode else ' major'),'key_correlation':score,'key_margin':score-keys[1][0],'onset_density_per_second':len(peaks)/dur,'loudness':loudness(f),'prediction_not_ground_truth':True}
  (root/'analysis'/f"{t['id']}.json").write_text(json.dumps(d,ensure_ascii=False,indent=2));summary[t['id']]={k:d[k] for k in ['duration','active_start','active_end','bpm','key_estimate','loudness']};(root/'analysis-receipt.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(t['id'],json.dumps(summary[t['id']],ensure_ascii=False),flush=True)
if __name__=='__main__':main()
