# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# This Dockerfile creates a developer image. It requires that the following things are mounted:
# - Mantid Imaging source at /opt/mantidimaging.

FROM centos:centos7

WORKDIR /opt/

RUN yum install -y make wget git which xorg-x11-server-Xvfb libxkbcommon-x11 fontconfig qt5-qtbase-devel &&\
    yum clean all

# Fixes "D-Bus library appears to be incorrectly set up;" error
RUN dbus-uuidgen > /var/lib/dbus/machine-id

RUN wget -nv -O Miniforge3.sh https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh &&\
    chmod +x Miniforge3.sh &&\
    bash Miniforge3.sh -b -p /opt/miniconda &&\
    rm Miniforge3.sh

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
