# syntax=docker/dockerfile:1
# Build the native CPU runtime against the same Debian generation used in production.
FROM python:3.11-slim-bookworm AS native-builder
ARG NEMO_CPP_REF=20999cc921d2b14aa58708f61756a8b2e787ba20
ARG PIP_PRIMARY_INDEX_URL=https://package-mirror.liara.ir/repository/pypi/simple
ARG PIP_FALLBACK_INDEX_URL=https://mirror2.chabokan.net/pypi/simple/
ARG APT_PRIMARY_DEBIAN_URL=https://mirror.metanet.ch/debian
ARG APT_PRIMARY_SECURITY_URL=https://mirror.metanet.ch/debian-security
ARG APT_FALLBACK_DEBIAN_URL=https://mirrors.huaweicloud.com/repository/debian
ARG APT_FALLBACK_SECURITY_URL=https://mirrors.huaweicloud.com/repository/debian-security
COPY ops/install-debian-packages.sh /usr/local/bin/install-debian-packages
RUN sh /usr/local/bin/install-debian-packages \
    git ca-certificates build-essential ninja-build pkg-config libsentencepiece-dev
# Install CMake via the same regional index failover used by other SuperApp modules.
RUN --mount=type=cache,id=superapp-diar-pip-cmake-py311,target=/root/.cache/pip,sharing=locked \
    set -eu; \
    if ! python -m pip install --disable-pip-version-check --timeout 15 --retries 2 \
        --index-url "$PIP_PRIMARY_INDEX_URL" cmake==3.30.9; then \
      echo 'Liara mirror failed while installing CMake; trying Chabokan'; \
      python -m pip install --disable-pip-version-check --timeout 15 --retries 2 \
        --index-url "$PIP_FALLBACK_INDEX_URL" cmake==3.30.9; \
    fi
RUN git clone https://github.com/NVIDIA/NeMo-Speech.cpp.git /src \
    && cd /src && git checkout "${NEMO_CPP_REF}" \
    && git submodule update --init llama.cpp
WORKDIR /src
RUN scripts/configure.sh cpu-diar \
    && cmake --build --preset cpu-diar --parallel 2 \
    && cmake --install build/cpu-diar --prefix /opt/nemo-speech \
    && test -x /opt/nemo-speech/bin/nemo-speech

FROM python:3.11-slim-bookworm
ARG PIP_PRIMARY_INDEX_URL=https://package-mirror.liara.ir/repository/pypi/simple
ARG PIP_FALLBACK_INDEX_URL=https://mirror2.chabokan.net/pypi/simple
ARG APT_PRIMARY_DEBIAN_URL=https://mirror.metanet.ch/debian
ARG APT_PRIMARY_SECURITY_URL=https://mirror.metanet.ch/debian-security
ARG APT_FALLBACK_DEBIAN_URL=https://mirrors.huaweicloud.com/repository/debian
ARG APT_FALLBACK_SECURITY_URL=https://mirrors.huaweicloud.com/repository/debian-security
COPY ops/install-debian-packages.sh /usr/local/bin/install-debian-packages
RUN sh /usr/local/bin/install-debian-packages \
    ffmpeg ca-certificates libstdc++6 libgomp1 libsentencepiece0
COPY --from=native-builder /opt/nemo-speech /opt/nemo-speech
ENV PATH="/opt/nemo-speech/bin:${PATH}" \
    LD_LIBRARY_PATH="/opt/nemo-speech/lib:/opt/nemo-speech/lib64" \
    NEMO_CLI_PATH="/opt/nemo-speech/bin/nemo-speech"
# Fail the image build if native shared libraries cannot be resolved.
RUN ldd /opt/nemo-speech/bin/nemo-speech | tee /tmp/native-deps.txt \
    && ! grep -q 'not found' /tmp/native-deps.txt \
    && /opt/nemo-speech/bin/nemo-speech --help >/dev/null
COPY backend/requirements.txt /app/requirements.txt
RUN --mount=type=cache,id=superapp-diar-pip-api-py311,target=/root/.cache/pip,sharing=locked \
    set -eu; \
    if ! python -m pip install --disable-pip-version-check --timeout 15 --retries 2 \
        --index-url "$PIP_PRIMARY_INDEX_URL" -r /app/requirements.txt; then \
      echo 'Liara mirror failed while installing API requirements; trying Chabokan'; \
      python -m pip install --disable-pip-version-check --timeout 15 --retries 2 \
        --index-url "$PIP_FALLBACK_INDEX_URL" -r /app/requirements.txt; \
    fi; \
    useradd -r -u 10001 app
COPY backend/app /app/app
WORKDIR /app
USER app
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","1"]
