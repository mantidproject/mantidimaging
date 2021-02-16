FROM mantidproject/mantidimaging:base

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh &&\
    chmod +x Miniconda3-latest-Linux-x86_64.sh &&\
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/miniconda &&\
    rm Miniconda3-latest-Linux-x86_64.sh

# Copy the requirement files into the docker image for installing the dependencies
COPY deps/dev-requirements.pip /opt/mantidimaging-deps/

SHELL ["/bin/bash", "-c"]

RUN eval "$(/opt/miniconda/bin/conda shell.bash hook)" &&\
    ENVIRONMENT_NAME=mantidimaging_test REPO_LABEL=unstable source <(curl -s https://raw.githubusercontent.com/mantidproject/mantidimaging/master/install.sh) &&\
    conda activate mantidimaging_test &&\
    pip install -r /opt/mantidimaging-deps/dev-requirements.pip &&\
    conda clean --all

RUN mkdir /opt/mantidimaging

ADD docker/entrypoint.sh /entrypoint.sh

WORKDIR /opt/mantidimaging
ENV MYPYPATH=/opt/mantidimaging
ENV PYTHONPATH=/opt/mantidimaging
ENV PATH=/opt/miniconda/bin:/opt/miniconda/condabin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV LD_LIBRARY_PATH=/opt/miniconda/lib/

VOLUME /opt/mantidimaging

ENTRYPOINT ["/entrypoint.sh"]
