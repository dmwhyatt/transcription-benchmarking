# YourMT3+ (Chang, Benetos, Kirchhoff and Dixon, MLSP 2024). GPL-3.0.
#
# A multi-instrument transcriber that claims singing without a separation
# front end. Its code is a pre-release: the authors point to their HuggingFace
# Space (issue #2 of github.com/mimbres/YourMT3), so this image takes amt/src
# from that Space at a pinned revision, code only -- the checkpoints there are
# Git LFS and are skipped here; the one this adapter uses is mounted at /ckpt.
#
# Checkpoint: "YPTF.MoE+Multi (noPS)", the Space's default and the one the
# authors name as best (issue #2, April 2026), with the Space's own arguments.
# Its training mix includes MIR-ST500 songs 1-400 (Spleeter vocals) and uses
# songs 401-500 as validation; see NOTES.md before reading its MIR-ST500 score.
#
# Versions: torch 2.2.2 is the Space's stated floor ("PyTorch>=2.2");
# transformers 4.45.1 and numpy 1.26.4 are the Space's own pins.
#
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
FROM pytorch/pytorch:2.2.2-cuda12.1-cudnn8-runtime

ARG DEBIAN_FRONTEND=noninteractive
ARG GIT_TERMINAL_PROMPT=0
ARG SPACE_REV=5e66c1ea173a8186e0d20432b841d3180cc015b5

RUN apt-get update \
 && apt-get install -y --no-install-recommends git git-lfs ca-certificates libsndfile1 \
 && rm -rf /var/lib/apt/lists/*

RUN GIT_LFS_SKIP_SMUDGE=1 git clone -q https://huggingface.co/spaces/mimbres/YourMT3 /tmp/space \
 && git -C /tmp/space checkout -q "$SPACE_REV" \
 && cp -r /tmp/space/amt/src /app \
 && cp /tmp/space/model_helper.py /app/model_helper.py \
 && echo "$SPACE_REV" > /app/REVISION \
 && rm -rf /tmp/space

RUN pip install --no-cache-dir \
      "transformers==4.45.1" "numpy==1.26.4" "pytorch-lightning==2.2.5" \
      "torchmetrics==1.4.0" "einops==0.8.0" "deprecated==1.2.14" \
      "librosa==0.10.2.post1" "mido==1.3.2" "pretty_midi==0.2.10" \
      "mir_eval==0.7" "wandb==0.17.9" "soundfile==0.12.1" "matplotlib==3.8.4" \
      "pyyaml" "tqdm" "requests" \
 && python -c "import torchaudio, sys; sys.path.insert(0, '/app'); \
import model_helper, utils.audio, utils.event2note, utils.note2event, utils.utils; \
print('imports ok, torchaudio', torchaudio.__version__)"

COPY adapter.py /adapter.py
ENV MPLCONFIGDIR=/cache WANDB_MODE=disabled HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
ENTRYPOINT ["python3", "/adapter.py"]
