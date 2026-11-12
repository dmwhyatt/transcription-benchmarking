# Tony (Mauch et al., TENOR 2015): its automatic note transcription, run headless.
# GPL-2.0 (Tony, pYIN); GPL-2.0-or-later (Sonic Annotator).
#
# Tony is a GUI for correcting a melody transcription, and the transcription it
# starts from is the pYIN Vamp plugin's "notes" output. This image runs that
# output through Sonic Annotator, the command-line Vamp host from the same
# group, with the parameters Tony itself sets (tony-notes.n3; see NOTES.md for
# where each value comes from).
#
# pYIN is built from source at the commit Tony pins in its repoint-lock.json
# (c4dm/pyin 1d68cac, the v1.2 tag commit), against Debian's Vamp SDK and
# Boost headers (pYIN's pitch HMM uses boost::math distributions). Sonic
# Annotator is its official "static" Linux release, checked against a sha256.
# That release is an AppImage, and AppImages need FUSE, which a container
# does not have, so it is unpacked at build time and run through its AppRun.
# The unpacked tree is owner-only, and the harness runs containers as the
# calling user rather than root, hence the chmod.
#
# CPU only: pYIN is YIN plus two small HMMs, with no network anywhere.
#
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints (unused: nothing to download)
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
FROM python:3.11-slim AS build

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git ca-certificates curl vamp-plugin-sdk libboost-dev \
    && rm -rf /var/lib/apt/lists/*

ARG PYIN_COMMIT=1d68cac9c5ecb1d81054d25d90158e5838dd78c2
RUN git clone https://github.com/c4dm/pyin.git /src/pyin \
    && cd /src/pyin && git checkout --detach "$PYIN_COMMIT" \
    && make -f Makefile.linux64 pyin.so \
    && git rev-parse HEAD > /src/pyin/REVISION

ARG SA_URL=https://github.com/sonic-visualiser/sonic-annotator/releases/download/sonic-annotator-1.7/sonic-annotator-1.7.0-linux64-static.tar.gz
ARG SA_SHA256=ec7838368aa6b20a039d04ebd5d91f4efd26e9c79f713b70843e35880151b919
RUN curl -fsSL -o /tmp/sa.tgz "$SA_URL" \
    && echo "$SA_SHA256  /tmp/sa.tgz" | sha256sum -c - \
    && tar xzf /tmp/sa.tgz -C /tmp \
    && cd /opt && /tmp/sonic-annotator-1.7.0-linux64-static/sonic-annotator --appimage-extract > /dev/null \
    && mv /opt/squashfs-root /opt/sonic-annotator \
    && cp /tmp/sonic-annotator-1.7.0-linux64-static/COPYING /opt/sonic-annotator/COPYING \
    && chmod -R a+rX /opt/sonic-annotator


FROM python:3.11-slim

# The AppImage bundles everything but libcom_err (Kerberos, pulled in by
# Qt's network module), which it expects from the host.
RUN apt-get update && apt-get install -y --no-install-recommends libcom-err2 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pretty_midi==0.2.10 soundfile==0.13.1 soxr==0.5.0.post1

COPY --from=build /opt/sonic-annotator /opt/sonic-annotator
COPY --from=build /src/pyin/pyin.so /src/pyin/pyin.cat /src/pyin/pyin.n3 /usr/local/lib/vamp/
COPY --from=build /src/pyin/REVISION /usr/local/lib/vamp/pyin.REVISION
# A wrapper, not a symlink: AppRun finds its libraries relative to $0.
RUN printf '#!/bin/sh\nexec /opt/sonic-annotator/AppRun "$@"\n' > /usr/local/bin/sonic-annotator \
    && chmod 755 /usr/local/bin/sonic-annotator
ENV VAMP_PATH=/usr/local/lib/vamp

COPY tony-notes.n3 /tony-notes.n3
COPY adapter.py /adapter.py
ENTRYPOINT ["python3", "/adapter.py"]
