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

# libhdf5-dev and pkg-config are for h5py. On this base pip does not use a
# wheel for it and falls back to compiling, which needs the HDF5 headers --
# mirst500 runs on the same image and never hit this because it needs no h5py.
RUN apt-get update && apt-get install -y --no-install-recommends \
        git ffmpeg libsndfile1 build-essential pkg-config libhdf5-dev \
    && rm -rf /var/lib/apt/lists/*

# Deliberately not requirements.txt. It lists spleeter, omnizart==0.5.0,
# madmom, cython, matplotlib and mir-eval -- none of which the inference path
# imports. spleeter is imported lazily inside do_svs_spleeter() and only when
# the config asks for separation; omnizart and madmom appear nowhere under
# do_everything.py, predictor.py, seq_dataset.py or get_feature.py, because
# they belong to the paper's comparison experiments. Installing them would
# mean a TF 1.x-era dependency tree for code that never runs.
# numpy first and alone, so that if h5py does compile it builds against the
# numpy that will be imported at run time rather than one pip swaps in
# afterwards -- the mismatch that shows up later as a binary-incompatibility
# error rather than as a failed build.
RUN pip install --no-cache-dir "numpy<2"
# h5py, and the two ways this went wrong are worth stating because they are
# the same two that bit crepe-notes and aubio here.
#
# A wheel first, and --only-binary so pip may not quietly fall back to
# compiling. h5py's wheels bundle their own HDF5, which makes this image
# independent of the 1.10.0 that Debian ships -- too old for current h5py,
# which wants >= 1.10.7. If no wheel exists for this interpreter, that is a
# fact worth failing on immediately rather than discovering through a
# compiler error.
#
# The fallback compiles, and must not do it under build isolation. Isolation
# builds a fresh environment, installs the newest numpy into it, and compiles
# the extension against numpy 2 headers -- which then meets numpy<2 at run
# time as "numpy.dtype size changed ... Expected 96 from C header, got 88".
# That install succeeds and the import fails, so it costs a whole sweep to
# find. --no-build-isolation compiles against the numpy already installed,
# which is the one that will be imported. 3.7.0 because it accepts HDF5
# 1.10.0.
RUN pip install --no-cache-dir --only-binary=:all: "h5py" \
 || ( pip install --no-cache-dir "setuptools" "wheel" "Cython" "pkgconfig" \
      && HDF5_DIR=/usr/lib/x86_64-linux-gnu/hdf5/serial \
         pip install --no-cache-dir --no-build-isolation "h5py==3.7.0" )

# numpy<2 repeated, not redundantly: without it pip is free to satisfy
# librosa by upgrading numpy to 2.x, which breaks the h5py just installed in
# exactly the way guarded against above. The import check is what would catch
# that, and it runs here so a bad combination fails the build rather than the
# sweep.
RUN pip install --no-cache-dir "librosa" "mido" "PyYAML" "tqdm" "numpy<2" \
    && python3 -c "import h5py, librosa, mido, yaml, numpy; \
print('h5py', h5py.__version__, '| numpy', numpy.__version__)"

ARG CTC_CE_REV=main
RUN git clone https://github.com/york135/CTC_CE_for_AST /app \
    && git -C /app checkout "$CTC_CE_REV" \
    && git -C /app rev-parse HEAD > /app/REVISION

COPY adapter.py /adapter.py
ENV HOME=/cache MPLCONFIGDIR=/cache NUMBA_CACHE_DIR=/cache
ENTRYPOINT ["python3", "/adapter.py"]
