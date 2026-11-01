# Architecture
Browser → Nginx/React → FastAPI → validated upload → ffmpeg mono PCM16 16kHz → pinned native nemo-speech CLI → normalized segments → JSON/RTTM.
One CPU inference request at a time by default. The CLI is launched per request and reloads weights; CPU latency requires evaluation. NeMo source pinned 20999cc921d2b14aa58708f61756a8b2e787ba20.
