# aubio. GPL-3.0. The floor, not a contender.
#
# Verified outside Docker, where it returned three notes for an eight-note
# legato phrase: its onset detector hears energy, not pitch change, so a slur
# becomes one long note. Kept in the sweep because a system that cannot beat
# this has a problem that no amount of interval arithmetic will fix.
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
FROM python:3.11-slim

RUN pip install --no-cache-dir aubio "numpy<2" pretty_midi

COPY adapter.py /adapter.py
ENTRYPOINT ["python3", "/adapter.py"]
