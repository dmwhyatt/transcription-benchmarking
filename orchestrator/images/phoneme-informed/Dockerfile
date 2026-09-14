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

RUN apt-get update && apt-get install -y --no-install-recommends git ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/seyong92/phoneme-informed-note-level-singing-transcription /app \
    && cd /app && git checkout b2fcd9ea0f7898a8989c7e65781052d1ffc81094

RUN pip install --no-cache-dir \
        "nnAudio==0.3.2" "mido>=1.2.10" "librosa==0.9.1" "numpy==1.23.4" \
        "wquantiles>=0.6" soundfile

COPY adapter.py /adapter.py
ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "/adapter.py"]
