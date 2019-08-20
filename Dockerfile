FROM ubuntu:18.04

WORKDIR /opt/

RUN apt update && apt install -y bzip2 wget && wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && bash Miniconda3-latest-Linux-x86_64.sh -b -f -p /opt/conda

# Set up a user `developer` with sudo rights
RUN export uid=1000 gid=1000 && \
    mkdir -p /home/developer && \
    mkdir -p /etc/sudoers.d/ && \
    echo "developer:x:${uid}:${gid}:Developer,,,:/home/developer:/bin/bash" >> /etc/passwd && \
    echo "developer:x:${uid}:" >> /etc/group && \
    echo "developer ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/developer && \
    chmod 0440 /etc/sudoers.d/developer && \
    chown ${uid}:${gid} -R /home/developer

RUN /opt/conda/bin/conda install -c conda-forge tomopy -y

RUN apt update && apt install -y git fontconfig \
      libglib2.0-0 \
      libxrandr2 \
      libxss1 \
      libxcursor1 \
      libxcomposite1 \
      libasound2 \
      libxi6 \
      libxtst6 \
      libsm6 \
      qt5-default

# RUN DEBIAN_FRONTEND=noninteractive apt install -y sudo xserver-xorg-video-nvidia-390 nvidia-driver-390 dbus-x11
# RUN DEBIAN_FRONTEND=noninteractive apt install -y sudo nvidia-384
RUN DEBIAN_FRONTEND=noninteractive apt install -y sudo nvidia-driver-390

# Move to being the user `developer`
USER developer
ENV HOME /home/developer
WORKDIR /home/developer

COPY mantidimaging mantidimaging

CMD ["/opt/conda/bin/python3", "-m", "mantidimaging"]

