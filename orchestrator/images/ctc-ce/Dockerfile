# CTC_CE_for_AST (Wang and Jang, TASLP 2022). york135's follow-up to the
# MIR-ST500 baseline, adding a CTC loss to cross-entropy.
#
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
#
# Weights are a Google Drive folder:
#   https://drive.google.com/drive/folders/1lxq-IF83cEXE8XsTFywNJhwtDSRXWqRx
# Take a checkpoint AND the config yaml that belongs to it. They are not
# interchangeable: upstream says the onset and offset thresholds are tuned per
# checkpoint and live in the config, so a mismatched pair transcribes at the
# wrong thresholds and still succeeds. `bench.py fetch` says this too.
#
# 1.13.1 rather than the requirements' torch==1.9.1: this is the tag mirst500
# already runs on here, so it is known good against the host driver, and the
# model code is ordinary torch with nothing version-specific in the inference
# path. If a checkpoint refuses to load, that pin is the first thing to try.
FROM pytorch/pytorch:1.13.1-cuda11.6-cudnn8-runtime

ARG DEBIAN_FRONTEND=noninteractive
ARG GIT_TERMINAL_PROMPT=0

RUN apt-get update && apt-get install -y --no-install-recommends \
        git ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Deliberately not requirements.txt. It lists spleeter, omnizart==0.5.0,
# madmom, cython, matplotlib and mir-eval -- none of which the inference path
# imports. spleeter is imported lazily inside do_svs_spleeter() and only when
# the config asks for separation; omnizart and madmom appear nowhere under
# do_everything.py, predictor.py, seq_dataset.py or get_feature.py, because
# they belong to the paper's comparison experiments. Installing them would
# mean a TF 1.x-era dependency tree for code that never runs.
RUN pip install --no-cache-dir \
        "librosa" "mido" "h5py" "PyYAML" "tqdm" "numpy<2"

ARG CTC_CE_REV=main
RUN git clone https://github.com/york135/CTC_CE_for_AST /app \
    && git -C /app checkout "$CTC_CE_REV" \
    && git -C /app rev-parse HEAD > /app/REVISION

COPY adapter.py /adapter.py
ENV HOME=/cache MPLCONFIGDIR=/cache NUMBA_CACHE_DIR=/cache
ENTRYPOINT ["python3", "/adapter.py"]
