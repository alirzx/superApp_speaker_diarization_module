# CPU-first speaker diarization architecture

```text
GitLab CI: git pull origin main && docker compose up --build -d
                                    |
                       model-setup (one-shot)
                          HF pinned download
                          SHA256 / manifest
                                    |
                   Docker named volume model_cache
                                    | (read-only)
                                    v
Browser -> UI Nginx -> API FastAPI -> upload validation -> ffmpeg WAV 16 kHz
                             -> nemo-speech diarize --device cpu
                             -> speaker segments -> normalized JSON or RTTM
```

The API starts only after model-setup exits successfully. API readiness
checks that native CLI exists and the pinned GGUF + manifest passed SHA256
validation at startup. UI starts after API health succeeds. Model cache
persists across container recreation and deployments; no model network
access occurs during inference.

Native source: NVIDIA/NeMo-Speech.cpp @ 20999cc921d2b14aa58708f61756a8b2e787ba20.
Model: nvidia/Nemotron-3-Diarization, revision
f667ed73aee57d40cc39428eb768b4fd87a0a29e,
Nemotron-3-Diarization.q8_0.gguf, SHA256
08456d9e22cd9a323c0364d98375f3746d6e68507ebb705cd46438c534c7a3a1.
The downloaded file and manifest are stored in /models; the Hugging Face
cache uses /models/.cache (persistent named volume).

API input accepts bounded audio files, generates temporary 16-kHz mono WAV,
and calls the native CLI in a subprocess per request. Speaker output is
validated, sorted, and exported in JSON or RTTM. Streaming APIs and speaker
identification are not implemented. Python and native components are
CPU-only and concurrency is bounded by a semaphore. This is not a
validated real-time latency configuration.

Service binds remain team-approved: local API 8003, LAN UI 8084.
The production UI host IP is set by UI_BIND_IP in the server's .env.
The optional pyannote and sherpa-onnx adapters are placeholders, not active.
