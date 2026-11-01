import os
from pathlib import Path
from app.services.model_manager import verify
verify(Path(os.getenv('MODEL_PATH','/models/Nemotron-3-Diarization.q8_0.gguf')),Path(os.getenv('MODEL_MANIFEST','/models/manifest.json')))
print('ok')
