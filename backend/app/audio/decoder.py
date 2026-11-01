import subprocess,wave
class InvalidAudio(ValueError):pass
def decode(source,dest,max_seconds,timeout):
    try:
        r=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-i',str(source),'-map','0:a:0','-vn','-ac','1','-ar','16000','-acodec','pcm_s16le','-t',str(max_seconds+1),str(dest)],capture_output=True,timeout=min(timeout,90),check=False)
        if r.returncode:raise InvalidAudio('audio decoder failed')
        with wave.open(str(dest),'rb') as w:
            if w.getnchannels()!=1 or w.getframerate()!=16000 or w.getsampwidth()!=2:raise InvalidAudio('bad PCM')
            duration=w.getnframes()/w.getframerate()
    except (subprocess.TimeoutExpired,OSError,wave.Error,EOFError) as e:raise InvalidAudio('invalid audio') from e
    if duration<=0 or duration>max_seconds:raise InvalidAudio('audio duration exceeds limit')
    return duration
