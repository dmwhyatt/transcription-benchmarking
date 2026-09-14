# CREPE Notes (Riley and Dixon, SMC 2023). GPL-3.0, and its madmom dependency
# restricts commercial use, which is conferred onto this image.
#
# Every line below exists because the documented install fails. The five
# blockers, in the order they appear, each confirmed by hitting it:
#
#   1. madmom's sdist does not declare Cython as a build requirement, and
#      pip's build isolation hides a preinstalled one -- hence
#      --no-build-isolation and the explicit Cython.
#   2. The PyPI madmom does not build on 3.10+ at all; the README's own fix is
#      to take it from git.
#   3. crepe's setup.py imports pkg_resources, removed in setuptools>=82. The
#      README calls this an Apple Silicon problem; it is not.
#   4. crepe_notes imports matplotlib without declaring it.
#   5. crepe-notes declares numpy>=2.0, which upgrades numpy out from under
#      madmom's compiled extensions: madmom then dies with "numpy.dtype size
#      changed". So numpy is forced back below 2 LAST, after everything else.
#      Verified: with numpy 1.26.4 both madmom and crepe_notes import.
#
# CREPE's weights are baked in at build time so the run needs no network.
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
FROM python:3.11-slim

# Build-time only, and both are about not hanging.
#
# tzdata's post-install asks for a geographic area, and ffmpeg pulls tzdata in.
# Under the legacy builder that prompt renders a menu and waits forever: not a
# failure that stops the build, a build that never finishes. ARG rather than
# ENV so it does not persist into the image and confuse apt at run time.
ARG DEBIAN_FRONTEND=noninteractive
# Likewise git: fail on a credential prompt instead of blocking on one.
ARG GIT_TERMINAL_PROMPT=0

RUN apt-get update && apt-get install -y --no-install-recommends \
        git build-essential libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "Cython<3" "numpy<2" "setuptools<81" wheel

RUN pip install --no-cache-dir --no-build-isolation \
        "git+https://github.com/CPJKU/madmom@main"

RUN pip install --no-cache-dir "tensorflow-cpu==2.15.1"
RUN pip install --no-cache-dir --no-build-isolation crepe

RUN pip install --no-cache-dir crepe-notes matplotlib

# Last, and deliberately so: see blocker 5 above.
RUN pip install --no-cache-dir "numpy<2" \
    && python3 -c "import madmom, crepe_notes; print('imports verified at build')"

# Bake CREPE's weights so the container needs no network at run time.
RUN python3 -c "import crepe; crepe.core.build_and_load_model('full')"

COPY adapter.py /adapter.py
ENV MPLCONFIGDIR=/cache TF_CPP_MIN_LOG_LEVEL=2 CREPE_NOTES_BACKEND=crepe
ENTRYPOINT ["python3", "/adapter.py"]
