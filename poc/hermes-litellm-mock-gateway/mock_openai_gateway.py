from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json, time
LOG = Path('/opt/data/workspace/hermes_litellm_poc_mock_requests.jsonl')
class H(BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A002 - matches BaseHTTPRequestHandler signature
        pass
    def _send(self, code, payload):
        body=json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path.endswith('/models'):
            self._send(200, {'object':'list','data':[{'id':'test-model','object':'model'}]})
        elif self.path == '/health':
            self._send(200, {'ok': True})
        else:
            self._send(404, {'error':'not found','path':self.path})
    def do_POST(self):
        n=int(self.headers.get('content-length','0') or 0)
        raw=self.rfile.read(n).decode('utf-8','replace')
        try: data=json.loads(raw)
        except Exception: data={'_raw':raw}
        rec={'ts':time.time(),'path':self.path,'headers':{k:v for k,v in self.headers.items() if k.lower() in ['authorization','x-litellm-user','x-user-id','content-type','user-agent']},'json':data}
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open('a',encoding='utf-8') as f: f.write(json.dumps(rec, ensure_ascii=False)+'\n')
        if self.path.endswith('/chat/completions'):
            if data.get('stream'):
                chunks = [
                    {'id':'chatcmpl-mock','object':'chat.completion.chunk','created':int(time.time()),'model':data.get('model','test-model'),'choices':[{'index':0,'delta':{'role':'assistant'},'finish_reason':None}]},
                    {'id':'chatcmpl-mock','object':'chat.completion.chunk','created':int(time.time()),'model':data.get('model','test-model'),'choices':[{'index':0,'delta':{'content':'MOCK_LITELLM_ROUTE_OK'},'finish_reason':None}]},
                    {'id':'chatcmpl-mock','object':'chat.completion.chunk','created':int(time.time()),'model':data.get('model','test-model'),'choices':[{'index':0,'delta':{},'finish_reason':'stop'}]},
                ]
                body = ''.join('data: '+json.dumps(c, ensure_ascii=False)+'\n\n' for c in chunks) + 'data: [DONE]\n\n'
                b = body.encode()
                self.send_response(200)
                self.send_header('Content-Type','text/event-stream')
                self.send_header('Content-Length',str(len(b)))
                self.end_headers(); self.wfile.write(b)
            else:
                self._send(200, {'id':'chatcmpl-mock','object':'chat.completion','created':int(time.time()),'model':data.get('model','test-model'),'choices':[{'index':0,'message':{'role':'assistant','content':'MOCK_LITELLM_ROUTE_OK'},'finish_reason':'stop'}],'usage':{'prompt_tokens':10,'completion_tokens':5,'total_tokens':15}})
        else:
            self._send(404, {'error':'not found','path':self.path})
if __name__ == '__main__':
    HTTPServer(('127.0.0.1', 40123), H).serve_forever()
