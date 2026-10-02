# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# This Dockerfile creates a developer image. It requires that the following things are mounted:
# - Mantid Imaging source at /opt/mantidimaging.

FROM rockylinux:8

WORKDIR /opt/

RUN yum install -y make wget git which xorg-x11-server-Xvfb libxkbcommon-x11 fontconfig qt5-qtbase-devel &&\
    yum clean all

# Fixes "D-Bus library appears to be incorrectly set up;" error
RUN dbus-uuidgen > /var/lib/dbus/machine-id

RUN curl -fsSL https://pixi.sh/install.sh | PIXI_VERSION=0.59.0 bash && mv /root/.pixi/bin/pixi /usr/local/bin/pixi

RUN mkdir /opt/mantidimaging

ADD docker/entrypoint.sh /entrypoint.sh

WORKDIR /opt/mantidimaging
ENV MYPYPATH=/opt/mantidimaging
ENV PYTHONPATH=/opt/mantidimaging

VOLUME /opt/mantidimaging

ENTRYPOINT ["/entrypoint.sh"]