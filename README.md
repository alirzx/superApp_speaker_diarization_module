# SuperApp Speaker Diarization

CPU-first standalone multilingual speaker diarization (Persian and English) using **NVIDIA Nemotron 3 Diarization**, **NeMo-Speech.cpp** and a React UI.

**Status:** implemented code and lightweight tests; real native model build, live inference, Persian DER, production load and commercial review must still be validated. Speaker labels identify recording-local turns, not real people.

## Quick start

```bash
cp .env.example .env
make model
make build
make up
curl http://127.0.0.1:8002/health/ready
```

UI: http://127.0.0.1:8083. API: `POST /v1/diarize` with multipart `file`, optional `output_format=json|rttm`. See docs/.

## Security

The API token must be set for production; do not expose the UI to untrusted networks without an identity-aware gateway and TLS. Runtime never downloads model weights. Audio is treated as confidential, with temporary storage and bounded uploads.
