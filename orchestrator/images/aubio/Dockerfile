# aubio. GPL-3.0. The floor, not a contender.
#
# Verified outside Docker, where it returned three notes for an eight-note
# legato phrase: its onset detector hears energy, not pitch change, so a slur
# becomes one long note. Kept in the sweep because a system that cannot beat
# this has a problem that no amount of interval arithmetic will fix.
#
# aubio ships NO linux wheel, in any release, so it always compiles and a slim
# image without a toolchain cannot install it. That is the whole fix. The
# toolchain lives in a builder stage and only the built wheel is carried
# forward, because this sweep runs on a disk with no room to spare.
#
# Two things were added on top of that and both broke the build, so neither is
# here now:
#
#   * python:3.9-slim, on a guess that 0.4.9 (2019) would not build against
#     3.11's C API. It builds against 3.11 fine -- confirmed twice, with pip
#     24.0 and with current pip.
#   * libsndfile1-dev, to widen the audio formats it can read. aubio's waf
#     build changes what it links when those headers are present, and the
#     verified-good build has no sndfile headers available at all.
#
# So the formats aubio reads here are the ones its own reader handles, which
# covers the WAV that vocadito and M4Singer ship. If a corpus of MP3 or FLAC
# needs transcribing, that is the knob to turn -- and to re-verify.
#
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
FROM python:3.11-slim AS build

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheels aubio==0.4.9


FROM python:3.11-slim

COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl "numpy<2" pretty_midi \
    && rm -rf /wheels \
    && python3 -c "import aubio; print('aubio', aubio.version)"

COPY adapter.py /adapter.py
ENTRYPOINT ["python3", "/adapter.py"]
