# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# This Dockerfile creates a developer image. It requires that the following things are mounted:
# - Mantid Imaging source at /opt/mantidimaging.

FROM ubuntu:22.04

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
    qtbase5-dev \
    qtchooser \
    xvfb &&\
    apt-get clean

RUN curl -fL --retry 3 \
    https://github.com/prefix-dev/pixi/releases/download/v0.59.0/pixi-x86_64-unknown-linux-musl.tar.gz \
    -o /tmp/pixi.tar.gz \
    && tar -xzf /tmp/pixi.tar.gz -C /tmp pixi \
    && install /tmp/pixi /usr/local/bin/pixi \
    && rm /tmp/pixi.tar.gz \
    && pixi --version

RUN mkdir /opt/mantidimaging

ADD docker/entrypoint.sh /entrypoint.sh

WORKDIR /opt/mantidimaging
ENV MYPYPATH=/opt/mantidimaging
ENV PYTHONPATH=/opt/mantidimaging

VOLUME /opt/mantidimaging

ENTRYPOINT ["/entrypoint.sh"]
