# STARS: Guo et al., Findings of ACL 2025 (arXiv 2507.06670). MIT. Pinned to f0e43e9.
#
# Built on ROSVOT by an overlapping group, but unlike ROSVOT it cannot run from
# audio alone: it force-aligns a phoneme sequence to the audio and feeds that
# alignment to its note decoder. So this image also carries the repository's own
# route for audio without lyrics (scripts/process_ch.py): FunASR's fsmn-vad to
# cut, SenseVoiceSmall to transcribe the lyrics, and scripts/mixedtext2phoneme.py
# to phonemise them. See adapter.py.
#
# Weights are mounted at /ckpt, from three ungated HuggingFace repos at pinned
# revisions (bench-work-stars-prep-20261112/ckpt/stars/fetch.sh):
#   rmvpe/model.pt, stars_chinese_english_bilingual/model_ckpt_steps_300000.ckpt
#     verstar/STARS @ 744a7ad
#   SenseVoiceSmall/     FunAudioLLM/SenseVoiceSmall @ 3847d57
#   fsmn-vad/            funasr/fsmn-vad @ df20e6b
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
#
# The README's tested stack is Python 3.10, PyTorch 2.4.0, CUDA 12 (cu124
# wheels), and that is what this is. torch's wheels carry their own CUDA, so a
# slim Python base needs only the host driver.
FROM python:3.10-slim

ARG DEBIAN_FRONTEND=noninteractive
ARG GIT_TERMINAL_PROMPT=0

# ffmpeg: pydub and FunASR fall back to it for anything that is not PCM WAV.
RUN apt-get update && apt-get install -y --no-install-recommends git ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/gwx314/STARS /app \
    && cd /app && git checkout f0e43e96cfe953f71a6cf9efd8b908b2c9d7e167

# PyPI stays the main index: with the PyTorch index as the only one, pip finds
# typing-extensions there as an sdist and cannot fetch its build backend.
RUN pip install --no-cache-dir "torch==2.4.0+cu124" "torchaudio==2.4.0+cu124" \
        --extra-index-url https://download.pytorch.org/whl/cu124

# requirements.txt is unpinned; these are its entries at versions that install
# on Python 3.10 beside torch 2.4, plus what the code imports but the file does
# not list (six, soundfile) and what process_ch.py and mixedtext2phoneme.py need
# (funasr, pydub, pypinyin, jieba). Deviations, recorded:
#   numpy<2 and scipy<1.14: utils/audio/vad.py imports scipy.ndimage.morphology.
#   scikit-image<0.25 and pyworld 0.3.5: later releases need Python 3.11.
#   g2p_en left out: nothing on the inference path imports it, and importing it
#     downloads NLTK data, which a container run offline cannot do.
# pyworld and webrtcvad compile, so a toolchain is installed and purged in the
# same layer.
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && pip install --no-cache-dir "numpy<2" "scipy<1.14" \
    && pip install --no-cache-dir "numpy<2" "scipy<1.14" "pyworld==0.3.5" "webrtcvad==2.0.10" \
        tensorboard pyyaml matplotlib "librosa==0.10.2.post1" "mir_eval==0.8.2" \
        "pretty_midi==0.2.11.post0" "pyloudnorm==0.2.0" "scikit-image<0.25" \
        "textgrid==1.6.1" "einops==0.8.2" praat-parselmouth "torchmetrics<1.9" six \
        soundfile "funasr==1.4.25" "pydub==0.25.1" "pypinyin==0.55.0" "jieba==0.42.1" \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -c "import pyworld, webrtcvad, funasr, pypinyin, jieba, pydub, torchaudio, librosa; print('stars deps ok')"

COPY adapter.py /adapter.py
ENV PYTHONPATH=/app MPLCONFIGDIR=/cache NUMBA_CACHE_DIR=/cache/numba
ENTRYPOINT ["python3", "/adapter.py"]
