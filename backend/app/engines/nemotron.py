import json,os,subprocess,tempfile
from pathlib import Path
from .base import DiarizationEngine
from ..services.model_manager import verify
class EngineError(RuntimeError):pass
class NemotronEngine(DiarizationEngine):
    def __init__(self,config):self.config=config;self.initialized=False
    def initialize(self):
        verify(self.config.model_path,self.config.manifest_path)
        if not self.config.cli_path.is_file() or not os.access(self.config.cli_path,os.X_OK):raise EngineError('native executable missing')
        self.initialized=True
    def diarize(self,wav):
        if not self.initialized:raise EngineError('engine not ready')
        with tempfile.TemporaryDirectory(prefix='nem-out-') as folder:
            output=Path(folder)/'result.json'
            args=[str(self.config.cli_path),'diarize',str(wav),'--model',str(self.config.model_path),'--device','cpu','--format','json','--output',str(output),'--preset','v3-streaming']
            env=dict(os.environ,OMP_NUM_THREADS=str(self.config.cpu_threads),OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
            try:r=subprocess.run(args,env=env,capture_output=True,timeout=self.config.inference_timeout,check=False)
            except (OSError,subprocess.TimeoutExpired) as e:raise EngineError('native inference unavailable') from e
            if r.returncode or not output.is_file():raise EngineError('native inference failed')
            try:data=json.loads(output.read_text())
            except (OSError,ValueError) as e:raise EngineError('malformed native JSON') from e
            if not isinstance(data,dict) or not isinstance(data.get('segments'),list):raise EngineError('unexpected native JSON schema')
            return data['segments']
