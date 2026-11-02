# Build the native CPU runtime against the same Debian generation used in production.
FROM python:3.11-slim-bookworm AS native-builder
ARG NEMO_CPP_REF=20999cc921d2b14aa58708f61756a8b2e787ba20
RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates build-essential ninja-build pkg-config libsentencepiece-dev \
    && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir cmake==3.30.9
RUN git clone https://github.com/NVIDIA/NeMo-Speech.cpp.git /src \
    && cd /src && git checkout "${NEMO_CPP_REF}" \
    && git submodule update --init llama.cpp
WORKDIR /src
RUN scripts/configure.sh cpu-diar \
    && cmake --build --preset cpu-diar --parallel 2 \
    && cmake --install build/cpu-diar --prefix /opt/nemo-speech \
    && test -x /opt/nemo-speech/bin/nemo-speech

FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg ca-certificates libstdc++6 libgomp1 libsentencepiece0 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=native-builder /opt/nemo-speech /opt/nemo-speech
ENV PATH="/opt/nemo-speech/bin:${PATH}" \
    LD_LIBRARY_PATH="/opt/nemo-speech/lib:/opt/nemo-speech/lib64" \
    NEMO_CLI_PATH="/opt/nemo-speech/bin/nemo-speech"
# Fail the image build if native shared libraries cannot be resolved.
RUN ldd /opt/nemo-speech/bin/nemo-speech | tee /tmp/native-deps.txt \
    && ! grep -q 'not found' /tmp/native-deps.txt \
    && /opt/nemo-speech/bin/nemo-speech --help >/dev/null
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && useradd -r -u 10001 app
COPY backend/app /app/app
WORKDIR /app
USER app
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","1"]
