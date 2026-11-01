import argparse,time
import httpx
p=argparse.ArgumentParser();p.add_argument('file');p.add_argument('--url',default='http://127.0.0.1:8002');p.add_argument('--token',default='');a=p.parse_args()
with open(a.file,'rb') as f:
    start=time.perf_counter();r=httpx.post(a.url+'/v1/diarize',files={'file':(a.file,f)},headers={'X-API-Key':a.token} if a.token else {},timeout=900);r.raise_for_status()
    print({'wall_seconds':round(time.perf_counter()-start,3),'response':r.json()})
