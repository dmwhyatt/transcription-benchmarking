# GAME: Generative Adaptive MIDI Extractor (OpenVPI). MIT.
#
# This image does NOT install GAME. Its releases publish ONNX bundles and
# nothing else -- no PyTorch checkpoint exists to download -- and its README
# says plainly: "We don't provide implementation of ONNX model inference
# pipeline in this repository." So infer.py cannot run the published weights,
# and adapter.py is that missing pipeline, written against ONNX.md.
#
# The consequence is a much smaller image: onnxruntime instead of torch on
# CUDA 12.9 takes this from roughly 11 GB to roughly 1 GB, which matters when
# nine images share one disk.
#
# CPU by default. onnxruntime-gpu would use the 3080, but the models are small
# and the encoder dominates; measure before paying for it.
#
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
FROM python:3.11-slim

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
        onnxruntime numpy soundfile soxr pretty_midi

COPY adapter.py /adapter.py
ENTRYPOINT ["python3", "/adapter.py"]
