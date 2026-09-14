# Omnizart's vocal module (VOCANO productionised, MCT Lab). MIT.
#
# Built on the upstream image rather than from pip, because pip install
# omnizart fails building pyaudio against a missing portaudio.h, and the
# published image has already solved that.
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
FROM mctlab/omnizart:latest

COPY adapter.py /adapter.py
ENTRYPOINT ["python3", "/adapter.py"]
