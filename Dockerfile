FROM continuumio/miniconda3

# Install prerequisites
# (see https://github.com/ContinuumIO/docker-images/issues/31)
RUN apt-get update && \
    apt-get install -y \
      git \
      fontconfig \
      libglib2.0-0 \
      libegl1-mesa \
      libgl1-mesa-glx \
      libxrandr2 \
      libxss1 \
      libxcursor1 \
      libxcomposite1 \
      libasound2 \
      libxi6 \
      libxtst6 \
      libsm6 && \
    conda install -y conda-build

# Get Mantid Imaging
ARG MANTIDIMAGING_REVISION=master
RUN git clone https://github.com/mantidproject/mantidimaging.git && \
    cd mantidimaging && \
    git checkout ${MANTIDIMAGING_REVISION}

# Install Mantid Imaging
RUN conda config --add channels intel && \
    conda config --add channels conda-forge && \
    conda-build /mantidimaging/conda/mantidimaging/ && \
    conda install -y -c /opt/conda/conda-bld mantidimaging

# Allow for custom versions of Mantid Imaging
RUN mkdir /mantidimaging_custom
ENV PYTHON_PATH=/mantidimaging_custom:${PYTHON_PATH}

# Add user
# RUN useradd -ms /bin/bash mantidimaging
# USER mantidimaging
# WORKDIR /home/mantidimaging

# Open GUI by default
CMD "mantidimaging"
