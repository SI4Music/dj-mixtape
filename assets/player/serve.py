from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import unquote,urlsplit
import argparse,mimetypes,re
ROOT=Path(__file__).resolve().parent
class Handler(BaseHTTPRequestHandler):
 def do_HEAD(self):self.serve(False)
 def do_GET(self):self.serve(True)
 def serve(self,body):
  p=(ROOT/(unquote(urlsplit(self.path).path).lstrip('/') or 'index.html')).resolve()
  if not p.is_relative_to(ROOT) or not p.is_file() or p.suffix not in ['.html','.css','.js','.json','.mp3']:self.send_error(404);return
  size=p.stat().st_size;start=0;end=size-1;partial=False;r=self.headers.get('Range')
  if r:
   m=re.fullmatch(r'bytes=(\d*)-(\d*)',r)
   if not m or not (m[1] or m[2]):self.send_error(416);return
   if m[1]:start=int(m[1]);end=min(size-1,int(m[2])) if m[2] else size-1
   else:start=max(0,size-int(m[2]))
   partial=True
   if start>=size or end<start:self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.send_header('Content-Length','0');self.end_headers();return
  self.send_response(206 if partial else 200);self.send_header('Content-Type',mimetypes.guess_type(p.name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(end-start+1));self.send_header('Accept-Ranges','bytes');self.send_header('Cache-Control','no-cache');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; media-src 'self'; object-src 'none'")
  if partial:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
  self.end_headers()
  if body:
   try:
    with p.open('rb') as f:
     f.seek(start);remain=end-start+1
     while remain:
      b=f.read(min(remain,65536))
      if not b:break
      self.wfile.write(b);remain-=len(b)
   except (BrokenPipeError,ConnectionResetError):pass
 def log_message(self,*args):pass
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=0);a=p.parse_args();server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);print(f'http://127.0.0.1:{server.server_port}/',flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:server.server_close()
