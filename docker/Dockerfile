FROM mantidproject/mantidimaging:base

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh &&\
    chmod +x Miniconda3-latest-Linux-x86_64.sh &&\
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/miniconda &&\
    rm Miniconda3-latest-Linux-x86_64.sh

SHELL ["/bin/bash", "-c"]

RUN eval "$(/opt/miniconda/bin/conda shell.bash hook)" &&\
    conda env create -n mantidimaging_test -f https://raw.githubusercontent.com/mantidproject/mantidimaging/855_cleanup_dependancy_handling/environment-dev.yml &&\
    conda activate mantidimaging_test &&\
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
