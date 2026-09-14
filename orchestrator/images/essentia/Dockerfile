# Essentia (MTG Barcelona). AGPL-3.0 -- which constrains anything downstream,
# not the measurement itself.
#
# The non-neural control: PredominantPitchMelodia into
# PitchContourSegmentation, no checkpoint, no GPU. Verified outside Docker,
# where it returned all eight synthetic notes with every onset within 22 ms.
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
FROM python:3.11-slim

RUN pip install --no-cache-dir essentia "numpy<2" pretty_midi

COPY adapter.py /adapter.py
ENTRYPOINT ["python3", "/adapter.py"]
