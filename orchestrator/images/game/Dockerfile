# GAME: Generative Adaptive MIDI Extractor (OpenVPI). MIT. Pinned to f423934.
#
# Upstream tests on Python 3.12 / torch 2.8 / CUDA 12.9, and its
# requirements.txt deliberately leaves torch to be installed by hand. Its
# numpy<2.0.0 pin is upstream's, not this image's.
#
# Weights come from GitHub releases or discussions; mount one at
# /ckpt/model.pt.
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
FROM pytorch/pytorch:2.8.0-cuda12.9-cudnn9-runtime

# Build-time only, and both are about not hanging.
#
# tzdata's post-install asks for a geographic area, and ffmpeg pulls tzdata in.
# Under the legacy builder that prompt renders a menu and waits forever: not a
# failure that stops the build, a build that never finishes. ARG rather than
# ENV so it does not persist into the image and confuse apt at run time.
ARG DEBIAN_FRONTEND=noninteractive
# Likewise git: fail on a credential prompt instead of blocking on one.
ARG GIT_TERMINAL_PROMPT=0

RUN apt-get update && apt-get install -y --no-install-recommends git ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/openvpi/GAME /app \
    && cd /app && git checkout f4239345f0fed21890d362c74a35fd857724aa82

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY adapter.py /adapter.py
ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "/adapter.py"]
