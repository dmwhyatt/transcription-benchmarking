# SOME: Singing-Oriented MIDI Extractor (OpenVPI). MIT.
#
# GAME's predecessor, and the reason to run it is the comparison: GAME scores
# the best onsets in the sweep and near-worst offsets, and SOME is the control
# that says whether that is the model family or this project's ONNX decoding.
#
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
#
# Weights are a release zip: github.com/openvpi/SOME/releases. Extract it so
# that /ckpt/some holds the .ckpt and the config.yaml that ships beside it --
# infer.py reads the config from the checkpoint's own directory, so they must
# stay together. `bench.py fetch` prints this.
#
# torch 2.1.2 rather than SOME's "2.1 or later": it is the tag this project
# already runs ROSVOT on, so it is known to work against the host driver.
FROM pytorch/pytorch:2.1.2-cuda11.8-cudnn8-runtime

ARG DEBIAN_FRONTEND=noninteractive
ARG GIT_TERMINAL_PROMPT=0

RUN apt-get update && apt-get install -y --no-install-recommends \
        git ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Deliberately not requirements.txt. That file is for training and the web UI,
# and it pins fairseq==0.12.2 -- which needs an old setuptools to build at all
# and is imported nowhere in the inference path. Tracing infer.py through
# inference/ and utils/ gives the list below and nothing else; gradio, onnx,
# tensorboard and MonkeyType are likewise training- or export-only.
RUN pip install --no-cache-dir \
        "click" \
        "einops==0.6.1" \
        "librosa<0.10.0" \
        "lightning>=2.0.0" \
        "mido" \
        "praat-parselmouth==0.4.3" \
        "PyYAML" \
        "scipy" \
        "torchmetrics" \
        "tqdm"

ARG SOME_REV=main
RUN git clone https://github.com/openvpi/SOME /app \
    && git -C /app checkout "$SOME_REV" \
    && git -C /app rev-parse HEAD > /app/REVISION

COPY adapter.py /adapter.py
ENV HOME=/cache MPLCONFIGDIR=/cache NUMBA_CACHE_DIR=/cache
ENTRYPOINT ["python3", "/adapter.py"]
