# MIR-ST500 baseline: Wang and Jang, ICASSP 2021. No licence file upstream --
# fine for measuring privately, not for anything downstream.
#
# Pinned to 6803137, the head on 5 March 2026. The pretrained EfficientNet-b0
# is committed to that repository, so this image carries its own weights and
# `bench.py fetch` has nothing to do.
#
# Two deviations from upstream requirement.txt, both deliberate:
#   * numpy is not pinned to 1.19.5, which has no wheels for this Python.
#   * spleeter is not installed. do_everything.py imports it only when -s is
#     passed, and vocadito is already solo voice. Rebuild with
#     --build-arg SPLEETER=1 for mixed audio; expect a TensorFlow fight.
#
# Note the model path is models/1005_e_4. The upstream README says
# model/1005_e_4, which does not exist.
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
FROM pytorch/pytorch:1.13.1-cuda11.6-cudnn8-runtime

ARG SPLEETER=0
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

RUN git clone --depth 1 https://github.com/york135/singing_transcription_ICASSP2021 /app \
    && cd /app && git fetch --depth 1 origin 680313740ec6792dc6358c3c722c63bd7d03159e \
    && git checkout 680313740ec6792dc6358c3c722c63bd7d03159e

RUN pip install --no-cache-dir "numpy<2" librosa soundfile tqdm mido ffmpeg-python \
    && if [ "$SPLEETER" = "1" ]; then pip install --no-cache-dir spleeter==1.5.4; fi

# net/effnet.py does torch.hub.load('rwightman/gen-efficientnet-pytorch', ...)
# and caching the repository is necessary but not sufficient.
#
# When the spec carries no ":ref", torch.hub works out the default branch by
# fetching https://github.com/<owner>/<repo>/tree/main/ -- and it does that
# BEFORE looking in the cache. So an offline container fails on name
# resolution however warm the cache is. Pinning the ref in the source skips
# that lookup entirely.
#
# trust_repo=True matters too: torch 1.13 prompts on an untrusted repo, and a
# prompt in a container with no terminal is a hang. Warming it here writes the
# trusted list alongside the cache.
ENV TORCH_HOME=/opt/torchhub
RUN sed -i "s|'rwightman/gen-efficientnet-pytorch'|'rwightman/gen-efficientnet-pytorch:master'|g" \
        /app/AST/net/effnet.py \
    && grep -q "gen-efficientnet-pytorch:master" /app/AST/net/effnet.py \
    && mkdir -p /opt/torchhub \
    && python3 -c "import torch; torch.hub.load('rwightman/gen-efficientnet-pytorch:master', 'efficientnet_b0', pretrained=False, trust_repo=True)" \
    && chmod -R a+rX /opt/torchhub

COPY adapter.py /adapter.py
ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "/adapter.py"]
