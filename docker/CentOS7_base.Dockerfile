# This Dockerfile creates a developer image. It requires that the following things are mounted:
# - Mantid Imaging source at /opt/mantidimaging.

FROM centos:centos7

WORKDIR /opt/

RUN yum install -y make wget git which xorg-x11-server-Xvfb libxkbcommon-x11 fontconfig qt5-qtbase-devel &&\
      yum clean all

# Fixes "D-Bus library appears to be incorrectly set up;" error
RUN dbus-uuidgen > /var/lib/dbus/machine-id
