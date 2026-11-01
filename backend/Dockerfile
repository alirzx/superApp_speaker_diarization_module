FROM ubuntu:24.04 AS native-builder
ARG NEMO_CPP_REF=20999cc921d2b14aa58708f61756a8b2e787ba20
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates build-essential ninja-build pkg-config libsentencepiece-dev python3 && rm -rf /var/lib/apt/lists/*
# The upstream native runtime requires CMake >= 3.26, install recent CMake in build layer only.
RUN apt-get update && apt-get install -y --no-install-recommends python3-pip python3-venv && python3 -m venv /opt/cmake && /opt/cmake/bin/pip install 'cmake==3.30.9' && rm -rf /var/lib/apt/lists/*
ENV PATH=/opt/cmake/bin:$PATH
RUN git clone https://github.com/NVIDIA/NeMo-Speech.cpp.git /src && cd /src && git checkout "$NEMO_CPP_REF" && git submodule update --init llama.cpp
WORKDIR /src
RUN scripts/configure.sh cpu-diar && cmake --build --preset cpu-diar --parallel 2
RUN find /src/build/cpu-diar -type f -name nemo-speech -executable -exec cp {} /tmp/nemo-speech \; && test -s /tmp/nemo-speech
FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libsentencepiece0 && rm -rf /var/lib/apt/lists/*
COPY --from=native-builder /tmp/nemo-speech /usr/local/bin/nemo-speech
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt && useradd -r -u 10001 app
COPY backend/app /app/app
WORKDIR /app
USER app
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","1"]
