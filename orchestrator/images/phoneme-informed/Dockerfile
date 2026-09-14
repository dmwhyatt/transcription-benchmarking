# A Phoneme-informed Neural Network Model for Note-level Singing
# Transcription: Yong et al., ICASSP 2023. MIT. Pinned to b2fcd9e.
#
# Worth running for its argument as much as its score: it feeds a phonetic
# posteriorgram alongside the mel spectrogram, on the grounds that singing
# onsets are linguistic events. That is the same phenomenon that put ROSVOT's
# notes 41 ms early against vocadito, approached as modelling rather than as
# a correction.
#
# Versions are the upstream pyproject's, not this image's choices: torch
# 1.13.1, torchaudio 0.13.1, nnAudio 0.3.2, librosa 0.9.1, numpy 1.23.4.
# The checkpoint is a release asset, so bench.py fetch can get it; it lands at
# /ckpt/model.pt.
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
FROM pytorch/pytorch:1.13.1-cuda11.6-cudnn8-runtime

# Build-time only, and both are about not hanging.
#
# tzdata's post-install asks for a geographic area, and ffmpeg pulls tzdata in.
# Under the legacy builder that prompt renders a menu and waits forever: not a
# failure that stops the build, a build that never finishes. ARG rather than
# ENV so it does not persist into the image and confuse apt at run time.
ARG DEBIAN_FRONTEND=noninteractive
# Likewise git: fail on a credential prompt instead of blocking on one.
ARG GIT_TERMINAL_PROMPT=0

RUN apt-get update && apt-get install -y --no-install-recommends git ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/seyong92/phoneme-informed-note-level-singing-transcription /app \
    && cd /app && git checkout b2fcd9ea0f7898a8989c7e65781052d1ffc81094

# torchaudio is NOT in the base image and infer.py imports it on line 5.
#
# It has to come from PyTorch's own cu116 index, not PyPI. PyPI's
# torchaudio 0.13.1 is built against CUDA 11.7 and refuses to load beside a
# CUDA 11.6 torch: "Detected that PyTorch and TorchAudio were compiled with
# different CUDA versions." There is no 1.13.1-cuda11.7 image to move to --
# pytorch/pytorch publishes only cuda11.6 for the whole 1.13 line.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu116 \
        "torchaudio==0.13.1"

RUN pip install --no-cache-dir \
        "nnAudio==0.3.2" "mido>=1.2.10" "librosa==0.9.1" "numpy==1.23.4" \
        "wquantiles>=0.6" soundfile \
    && python3 -c "import torch, torchaudio; print('torch', torch.__version__, 'torchaudio', torchaudio.__version__)"

COPY adapter.py /adapter.py
ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "/adapter.py"]
