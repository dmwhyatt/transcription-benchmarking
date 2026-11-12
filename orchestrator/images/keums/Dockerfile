# Kum et al., ICASSP 2022: pseudo-label transfer in a teacher-student
# framework. Companion code, no licence file upstream -- treat as
# research-use-only until the authors say otherwise.
#
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
#
# CPU-only on purpose. TF 2.5 wants CUDA 11.2 with cuDNN 8.1 exactly, and
# pairing those inside a container is a bigger risk than the time it saves:
# this is a ResNet over 40 short recordings, which CPU handles.
#
# The weights ship in the repository (data/weight_ST.hdf5, 17.5 MB), so the
# run needs no network and no /ckpt mount.
FROM python:3.9-slim

# python 3.9 because tensorflow 2.5 published cp36-cp39 wheels and nothing later.
ARG DEBIAN_FRONTEND=noninteractive
ARG GIT_TERMINAL_PROMPT=0

# ffmpeg for pydub, libsndfile1 for librosa's soundfile backend.
RUN apt-get update && apt-get install -y --no-install-recommends \
        git ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Deliberately NOT requirements.txt. It pins keras==2.7.0 alongside
# tensorflow==2.5.0, and the code imports tensorflow.keras rather than keras --
# so that pin installs a second, newer Keras that the model never uses and
# that can shadow the bundled one. Everything else here is its pinning.
RUN pip install --no-cache-dir \
        "tensorflow==2.5.0" \
        "numpy==1.19.5" \
        "scipy==1.7.3" \
        "librosa==0.8.1" \
        "pydub==0.25.1" \
        "pretty-midi==0.2.9" \
        "mir_eval==0.6" \
        "matplotlib==3.5.3"

# matplotlib is not librosa's dependency -- it belongs to the [display] extra --
# but quantization.py and MIDI.py both import librosa.display, so this code
# needs it and nothing declares it. Pinned rather than free: librosa 0.8.1's
# display module does `from matplotlib.cm import get_cmap`, which matplotlib
# removed in 3.9, so an unpinned install resolves to a version that cannot
# import. 3.5.3 is the last line that supports python 3.9 and leaves
# numpy 1.19.5 alone.

# No pin available offline -- override with --build-arg KEUMS_REV=<sha> once a
# build is known good. The commit actually used is recorded in adapter.json
# either way, so a run can always be traced to a revision.
ARG KEUMS_REV=main
RUN git clone https://github.com/keums/icassp2022-vocal-transcription /app \
    && git -C /app checkout "$KEUMS_REV" \
    && git -C /app rev-parse HEAD > /app/REVISION \
    && test -s /app/data/weight_ST.hdf5

COPY adapter.py /adapter.py
# MPLBACKEND because quantization.py imports pyplot and there is no display
# here; without it matplotlib picks an interactive backend and fails.
ENV HOME=/cache MPLCONFIGDIR=/cache NUMBA_CACHE_DIR=/cache \
    MPLBACKEND=Agg TF_CPP_MIN_LOG_LEVEL=2 PYTHONPATH=/app/src
ENTRYPOINT ["python3", "/adapter.py"]
