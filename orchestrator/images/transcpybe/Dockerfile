# transcPybe -- the transcriber this benchmark was built alongside.
#
# Unlike every other image here, the source is NOT cloned during the build:
# dmwhyatt/transcpybe is private, and a Dockerfile has no credentials. So this
# image is built with a local checkout as its build context, which `bench.py
# build` arranges -- see build_context_env in systems.py. Point TRANSCPYBE_SRC
# at the checkout, or keep it beside this repository as ../transcpybe.
#
# Its own dependencies are all on PyPI. The transcription-benchmarking
# requirement lives in the "tune" extra, not the default install, so nothing
# here needs credentials either -- and scoring is this benchmark's job anyway.
#
# The crepe extra is installed because it is the accurate backend and the
# reason the tool has a --device flag. torchcrepe ships its model weights
# inside the wheel, so the container still needs no network at run time.
#
# Contract, identical for every image in this directory:
#   /audio  read-only corpus, nested directories preserved
#   /ckpt   read-only checkpoints
#   /cache  writable scratch (also $HOME)
#   /out    writable; must contain midi/<same relative path>.mid and adapter.json
FROM pytorch/pytorch:2.8.0-cuda12.9-cudnn9-runtime

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends libsndfile1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY . /src
RUN pip install --no-cache-dir "/src[crepe]" \
    && transcpybe --help > /dev/null \
    && python3 -c "import torchcrepe; print('torchcrepe', torchcrepe.__version__ if hasattr(torchcrepe,'__version__') else 'ok')"

# Every other image COPYs its adapter in as well as having it mounted. This
# one cannot: the build context is the transcPybe checkout, and the adapter
# lives in this repository. bench.py mounts it at /adapter.py on every run, so
# the image works there and only there -- a bare `docker run bench/transcpybe`
# will not find it, which this comment exists to explain.
ENV MPLCONFIGDIR=/cache
ENTRYPOINT ["python3", "/adapter.py"]
