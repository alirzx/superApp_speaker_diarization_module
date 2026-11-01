import hashlib,json
from pathlib import Path
REV='f667ed73aee57d40cc39428eb768b4fd87a0a29e'
SHA='08456d9e22cd9a323c0364d98375f3746d6e68507ebb705cd46438c534c7a3a1'
NAME='Nemotron-3-Diarization.q8_0.gguf'
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def verify(path,manifest):
    m=json.loads(Path(manifest).read_text())
    if m.get('revision')!=REV or m.get('sha256')!=SHA or m.get('filename')!=Path(path).name:raise ValueError('model manifest mismatch')
    if digest(path)!=SHA:raise ValueError('model hash mismatch')
