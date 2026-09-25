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


RUN curl -fsSL https://pixi.sh/install.sh | PIXI_VERSION=0.59.0 bash && mv /root/.pixi/bin/pixi /usr/local/bin/pixi

RUN mkdir /opt/mantidimaging

ADD docker/entrypoint.sh /entrypoint.sh

WORKDIR /opt/mantidimaging
ENV MYPYPATH=/opt/mantidimaging
ENV PYTHONPATH=/opt/mantidimaging

VOLUME /opt/mantidimaging

ENTRYPOINT ["/entrypoint.sh"]
