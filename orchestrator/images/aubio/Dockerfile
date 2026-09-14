# aubio. GPL-3.0. The floor, not a contender.
#
# Verified outside Docker, where it returned three notes for an eight-note
# legato phrase: its onset detector hears energy, not pitch change, so a slur
# becomes one long note. Kept in the sweep because a system that cannot beat
# this has a problem that no amount of interval arithmetic will fix.
#
# Three things this image has to get right, each learned from a failed build.
#
# 1. aubio ships NO linux wheel, in any release, so it always compiles and a
#    slim image without a toolchain cannot install it. The toolchain lives in
#    a builder stage and only the finished wheel is carried forward, because
#    this sweep runs on a disk with no room to spare.
#
# 2. CFLAGS. aubio 0.4.9 declares its ufunc callbacks as
#        void (*)(char **, npy_intp *, npy_intp *, void *)
#    which numpy changed to const npy_intp * in 1.25. GCC 13 calls that
#    mismatch a warning; GCC 14 -- which this base image now carries -- makes
#    it an error, and the build dies in ufuncs.c. Pinning numpy does not help:
#    every numpy from 1.25 onward has the const signature. The mismatch is
#    only a const qualifier on a pointer argument, so it is ABI-identical and
#    demoting it back to a warning is safe. Confirmed by building with the
#    diagnostic forced fatal and this flag demoting it, then running the
#    result.
#
# 3. numpy is NOT pinned here, unlike most images in this directory. The wheel
#    is built against whatever numpy the build environment resolves, so the
#    runtime must not then be dragged to a different major version underneath
#    it. Build and run agree by saying nothing.
#
# aubio reads the formats its own reader handles, which covers the WAV that
# vocadito and M4Singer ship. libsndfile headers would widen that, and would
# also change what its waf build links -- so that is a knob to turn with a
# re-verified build, not a line to add hopefully.
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

ENV CFLAGS="-Wno-error=incompatible-pointer-types"
RUN pip wheel --no-cache-dir --wheel-dir /wheels aubio==0.4.9


FROM python:3.11-slim

COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/aubio-*.whl pretty_midi \
    && rm -rf /wheels \
    && python3 -c "import numpy, aubio; print('aubio', aubio.version, 'on numpy', numpy.__version__)"

COPY adapter.py /adapter.py
ENTRYPOINT ["python3", "/adapter.py"]
