FROM ubuntu:18.04

WORKDIR /opt/

RUN apt-get update && apt-get install -y wget git fontconfig \
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


RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh &&\
    chmod +x Miniconda3-latest-Linux-x86_64.sh &&\
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/miniconda

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
    # pip install PyQt5 python-engineio==3.9.3 h5py==2.9.0

# RUN DEBIAN_FRONTEND=noninteractive apt install -y sudo xserver-xorg-video-nvidia-390 nvidia-driver-390 dbus-x11
# RUN DEBIAN_FRONTEND=noninteractive apt install -y sudo nvidia-384
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y sudo nvidia-driver-390

# Set up a user `developer` with sudo rights
# RUN export uid=1000 gid=1000 && \
#     mkdir -p /home/developer && \
#     mkdir -p /etc/sudoers.d/ && \
#     echo "developer:x:${uid}:${gid}:Developer,,,:/home/developer:/bin/bash" >> /etc/passwd && \
#     echo "developer:x:${uid}:" >> /etc/group && \
#     echo "developer ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/developer && \
#     chmod 0440 /etc/sudoers.d/developer && \
#     chown ${uid}:${gid} -R /home/developer

RUN mkdir /opt/mantidimaging

# # Move to being the user `developer`
# USER developer
# ENV HOME /home/developer
WORKDIR /opt/mantidimaging
ENV MYPYPATH=/opt/mantidimaging
ENV PATH=/opt/miniconda/bin:/opt/miniconda/condabin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

CMD eval "$(/opt/miniconda/bin/conda shell.bash hook)" &&\
    python -m mantidimaging


