import json,os
from pathlib import Path
from huggingface_hub import hf_hub_download
from app.services.model_manager import REV,SHA,NAME,digest
p=Path(os.getenv('MODEL_DIR','/models'));p.mkdir(parents=True,exist_ok=True)
target=p/NAME
if not target.exists() or digest(target)!=SHA:
    source=Path(hf_hub_download(repo_id='nvidia/Nemotron-3-Diarization',revision=REV,filename=NAME))
    if digest(source)!=SHA:raise SystemExit('Model digest mismatch')
    import shutil
    tmp=p/(NAME+'.partial');shutil.copyfile(source,tmp);os.replace(tmp,target)
(p/'manifest.json').write_text(json.dumps(dict(revision=REV,sha256=SHA,filename=NAME),indent=2)+'\n')
print('Pinned model verified')
