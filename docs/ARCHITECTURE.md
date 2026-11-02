# Architecture

```text
User audio -> React + Nginx /api -> FastAPI /v1/diarize
          -> upload validation -> ffmpeg mono PCM16 16kHz
          -> NVIDIA NeMo-Speech.cpp native CLI --device cpu
          -> Nemotron 3 Diarization Q8 GGUF
          -> segment schema validation -> JSON / RTTM -> speaker timeline
```

Five API paths: /health/live, /health/ready, /v1/models,
POST /v1/diarize, /metrics. The API uses one Uvicorn worker and
a concurrency semaphore (default 1). Speaker IDs are local anonymous
slots; up to eight speaker slots, overlapping segments preserved.
pyannote and sherpa-onnx files are placeholder backends, not active models.

## Runtime and model lifecycle

- Separate setup container retrieves pinned NVIDIA GGUF from Hugging Face
  and verifies immutable SHA256. Mounted /models volume is read-only in API.
- Native source pinned to NeMo-Speech.cpp commit
  20999cc921d2b14aa58708f61756a8b2e787ba20.
- Native builder and runtime share the Debian Bookworm ABI family.
  CMake installs the complete native binaries and shared libraries into
  /opt/nemo-speech; runtime LD_LIBRARY_PATH points to that installation.
- API does not perform downloads per request. It validates model manifest
  and SHA256 at startup.
- Each request launches a separate native CLI process: this incurs
  potential repeated model loading. Future persistent C ABI/server support
  requires separate profiling and integration tests.
- Audio is decoded in an ephemeral request-local directory and deleted.
  Upload byte limit, decoded duration limit, queue timeout and inference
  subprocess timeout are all applied.

The CPU/RAM/concurrency settings are initial guesses requiring actual
measurements; no real Persian/English performance benchmark is claimed.
