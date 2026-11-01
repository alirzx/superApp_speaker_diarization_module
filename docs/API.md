# API
`GET /health/live`, `GET /health/ready`, `GET /v1/models`, `GET /metrics`, `POST /v1/diarize`.
Diarize accepts multipart `file`, optional `output_format=json|rttm`, `request_id`. JSON fields: request_id, status, model, runtime, audio_duration_seconds, num_speakers, speakers, segments, processing_time_ms. IDs are local to recording and overlap is preserved.
