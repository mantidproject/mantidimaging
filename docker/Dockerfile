# This Dockerfile creates a developer image. It requires that the following things are mounted:
# - Mantid Imaging source at /opt/mantidimaging.
# It also requires the DISPLAY environment variable and sharing the X11 socket via
# -v /tmp/.X11-unix:/tmp/.X11-unix:ro
FROM ubuntu:18.04

WORKDIR /opt/

RUN apt-get update && apt-get install -y make wget git fontconfig \
      libglib2.0-0 \
      libxrandr2 \
      libxss1 \
      libxcursor1 \
      libxcomposite1 \
      libasound2 \
      libxi6 \
      libxtst6 \
      libsm6 \
      qt5-default &&\
      apt-get clean

# RUN DEBIAN_FRONTEND=noninteractive apt-get install -y nvidia-driver-390 && apt-get clean

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh &&\
    chmod +x Miniconda3-latest-Linux-x86_64.sh &&\
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/miniconda &&\
    rm Miniconda3-latest-Linux-x86_64.sh

# Copy the requirement files into the docker image for installing the dependencies
COPY deps/pip-requirements.txt deps/dev-requirements.pip /opt/mantidimaging-deps/

RUN eval "$(/opt/miniconda/bin/conda shell.bash hook)" &&\
    conda init &&\
    conda config --set always_yes yes --set changeps1 no &&\
    conda config --prepend channels conda-forge &&\
    conda config --prepend channels anaconda &&\
    conda config --prepend channels defaults &&\
    conda install --only-deps -c dtasev mantidimaging && \
    pip install -r /opt/mantidimaging-deps/pip-requirements.txt &&\
    pip install -r /opt/mantidimaging-deps/dev-requirements.pip &&\
    conda clean --all

RUN mkdir /opt/mantidimaging

WORKDIR /opt/mantidimaging
ENV MYPYPATH=/opt/mantidimaging
ENV PYTHONPATH=/opt/mantidimaging
ENV PATH=/opt/miniconda/bin:/opt/miniconda/condabin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

CMD eval "$(/opt/miniconda/bin/conda shell.bash hook)" &&\
    python -m mantidimaging


