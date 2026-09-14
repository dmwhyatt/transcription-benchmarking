# ROSVOT: Li et al., ACL 2024. MIT. Pinned to 3c8332b.
#
# Install follows the repository's own scripts/install.sh rather than a
# requirements.txt, because its authors say sharing one is prone to dependency
# issues. Inference needs far less than training, so only the inference set is
# installed here.
#
# Weights are a Google Drive zip that Drive rate-limits, so this image expects
# them mounted at /ckpt: rosvot/model.pt, rwbd/model.pt, rmvpe/.
# `bench.py fetch` prints the instructions.
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
# ROSVOT asks for torch 2.1.1, which pytorch/pytorch never published; 2.1.2 is
# the neighbouring tag, confirmed present in the registry.
FROM pytorch/pytorch:2.1.2-cuda11.8-cudnn8-runtime

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

RUN git clone https://github.com/RickyL-2000/ROSVOT /app \
    && cd /app && git checkout 3c8332bf43adae35f6e4d64971862f2f6139b310

# pyworld has no wheel for any Python this base image is likely to carry, so
# it compiles -- which needs a toolchain and, being a Cython extension, Cython
# and numpy present before it builds. The toolchain is purged in the same
# layer so it does not survive into an 8 GB image.
#
# matplotlib is loosened from ROSVOT's own ==3.5. That pin has no wheel past
# cp310 and would have to build from source; 3.7 is the nearest version with
# wheels everywhere. ROSVOT wants matplotlib for training-time plots, and this
# image only ever runs inference -- but it is a deviation from upstream and is
# recorded as one.
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && pip install --no-cache-dir "Cython<3" "numpy<2" \
    && pip install --no-cache-dir "pyworld==0.2.12" \
    && pip install --no-cache-dir librosa tqdm "matplotlib<3.8" pyyaml \
        pretty_midi scipy einops \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -c "import pyworld, librosa, pretty_midi; print('rosvot deps ok')"

COPY adapter.py /adapter.py
ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "/adapter.py"]
