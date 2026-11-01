from time import perf_counter
from uuid import uuid4
from ..audio.decoder import decode
from ..audio.postprocessing import normalize
def run(engine,config,source,wav,request_id=None):
    start=perf_counter();duration=decode(source,wav,config.max_audio_seconds,config.inference_timeout)
    segments=normalize(engine.diarize(wav),duration);speakers=sorted({s['speaker_id'] for s in segments})
    return {'request_id':request_id or str(uuid4()),'status':'completed','model':'nvidia/Nemotron-3-Diarization','runtime':'cpu','audio_duration_seconds':round(duration,3),'num_speakers':len(speakers),'speakers':speakers,'segments':segments,'processing_time_ms':round((perf_counter()-start)*1000,2)}
