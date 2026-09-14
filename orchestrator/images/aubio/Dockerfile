# aubio. GPL-3.0. The floor, not a contender.
#
# Verified outside Docker, where it returned three notes for an eight-note
# legato phrase: its onset detector hears energy, not pitch change, so a slur
# becomes one long note. Kept in the sweep because a system that cannot beat
# this has a problem that no amount of interval arithmetic will fix.
#
# Two things make this image less trivial than it looks, both learned by the
# build failing:
#
#   * aubio ships NO linux wheels, in any release. It always compiles, so a
#     slim image without a toolchain cannot install it. The toolchain lives in
#     a builder stage and only the built wheel is carried forward, which keeps
#     the final image small -- this sweep runs on a disk with no room to spare.
#   * 0.4.9 is the latest release and dates from 2019, which is before Python
#     3.11. Building it there is a gamble against old C API use, so this
#     pins 3.9, where it is known good. Nothing else in the image cares.
#
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
FROM python:3.9-slim AS build

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential pkg-config libsndfile1-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip wheel --no-cache-dir --wheel-dir /wheels aubio==0.4.9


FROM python:3.9-slim

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl "numpy<2" pretty_midi \
    && rm -rf /wheels \
    && python3 -c "import aubio; print('aubio', aubio.version)"

COPY adapter.py /adapter.py
ENTRYPOINT ["python3", "/adapter.py"]
