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
