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

# omnizart's vocal app fetches a sherpa-onnx Spleeter model on first use and
# writes it inside its own site-packages directory. At run time this container
# is non-root and has no network, so that attempt dies with PermissionError on
# .../omnizart/checkpoints/vocal/sherpa-onnx-spleeter-2stems-fp16.
#
# Do it here instead, as root and with a network: transcribe one second of
# silence, purely so the lazy download happens now and the result is baked in.
# The transcription itself is allowed to fail -- the model is fetched before
# any of it is used, and silence is not a fair test of anything.
RUN python3 -c "import wave; \
        w = wave.open('/tmp/warm.wav', 'wb'); \
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100); \
        w.writeframes(b'\x00\x00' * 44100); w.close()" \
    && (omnizart vocal transcribe /tmp/warm.wav -o /tmp/warm || true) \
    && rm -rf /tmp/warm.wav /tmp/warm \
    && chmod -R a+rX /usr/local/lib/python3.11/dist-packages/omnizart/checkpoints \
       2>/dev/null || true

COPY adapter.py /adapter.py
ENTRYPOINT ["python3", "/adapter.py"]
