# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# This Dockerfile creates a developer image. It requires that the following things are mounted:
# - Mantid Imaging source at /opt/mantidimaging.

FROM ubuntu:18.04

WORKDIR /opt/

RUN apt-get update && apt-get install -y make wget curl git fontconfig \
    libglib2.0-0 \
    libxrandr2 \
    libxss1 \
    libxcursor1 \
    libxcomposite1 \
    libasound2 \
    libxi6 \
    libxtst6 \
    libsm6 \
    qt5-default \
    xvfb &&\
    apt-get clean


RUN wget -nv -O Mambaforge.sh https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh &&\
    chmod +x Mambaforge.sh &&\
    bash Mambaforge.sh -b -p /opt/miniconda &&\
    rm Mambaforge.sh

SHELL ["/bin/bash", "-c"]

RUN --mount=type=bind,target=/src \
    cd /src &&\
    eval "$(/opt/miniconda/bin/conda shell.bash hook)" &&\
    python3 ./setup.py create_dev_env &&\
    mamba clean --all

RUN mkdir /opt/mantidimaging

ADD docker/entrypoint.sh /entrypoint.sh

WORKDIR /opt/mantidimaging
ENV MYPYPATH=/opt/mantidimaging
ENV PYTHONPATH=/opt/mantidimaging
ENV PATH=/opt/miniconda/bin:/opt/miniconda/condabin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV LD_LIBRARY_PATH=/opt/miniconda/lib/

VOLUME /opt/mantidimaging

ENTRYPOINT ["/entrypoint.sh"]
