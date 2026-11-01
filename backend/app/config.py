from dataclasses import dataclass
from pathlib import Path
import os
@dataclass(frozen=True)
class Settings:
    environment: str=os.getenv('APP_ENV','development')
    api_token: str=os.getenv('API_TOKEN','')
    model_path: Path=Path(os.getenv('MODEL_PATH','/models/Nemotron-3-Diarization.q8_0.gguf'))
    manifest_path: Path=Path(os.getenv('MODEL_MANIFEST','/models/manifest.json'))
    cli_path: Path=Path(os.getenv('NEMO_CLI_PATH','/usr/local/bin/nemo-speech'))
    max_upload_mb:int=int(os.getenv('MAX_UPLOAD_MB','25'))
    max_audio_seconds:int=int(os.getenv('MAX_AUDIO_SECONDS','300'))
    cpu_threads:int=int(os.getenv('CPU_THREADS','2'))
    concurrency:int=int(os.getenv('MAX_CONCURRENT_INFERENCE','1'))
    queue_timeout:float=float(os.getenv('MAX_QUEUE_WAIT_SECONDS','10'))
    inference_timeout:float=float(os.getenv('INFERENCE_TIMEOUT_SECONDS','600'))
    def validate(self):
        if self.environment not in ('development','test','production'):raise ValueError('invalid APP_ENV')
        if self.environment=='production' and len(self.api_token)<32:raise ValueError('strong production token required')
        if not 1<=self.max_upload_mb<=512 or not 1<=self.max_audio_seconds<=7200:raise ValueError('invalid media bounds')
        if not 1<=self.cpu_threads<=64 or not 1<=self.concurrency<=16:raise ValueError('invalid CPU limits')
        if self.queue_timeout<=0 or self.inference_timeout<=0:raise ValueError('invalid timeouts')
