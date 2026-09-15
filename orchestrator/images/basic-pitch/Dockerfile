# Basic Pitch (Spotify, ICASSP 2022). Apache-2.0.
#
# The one install in this directory that was verified outside Docker: a plain
# pip install into a clean 3.11 venv, which then transcribed a synthetic sung
# phrase 8/8. Model weights ship inside the wheel, so the run needs no network.
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
FROM python:3.11-slim

RUN pip install --no-cache-dir "basic-pitch[tf]==0.4.0"

COPY adapter.py /adapter.py
ENV MPLCONFIGDIR=/cache TF_CPP_MIN_LOG_LEVEL=2
ENTRYPOINT ["python3", "/adapter.py"]
