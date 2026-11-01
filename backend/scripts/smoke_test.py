import os,urllib.request
base=os.getenv('API_URL','http://127.0.0.1:8002')
for path in ['/health/live','/health/ready']:
    with urllib.request.urlopen(base+path,timeout=10) as r:print(path,r.status,r.read().decode())
