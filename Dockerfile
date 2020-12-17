FROM freesurfer/freesurfer:7.1.1 as base

LABEL maintainer="support@flywheel.io"

RUN yum clean all -y \
  && yum update -y \
  && yum install -y unzip \
  && yum clean all -y

RUN source $FREESURFER_HOME/SetUpFreeSurfer.sh

# extra segmentations require matlab compiled runtime
RUN fs_install_mcr R2014b

# Save environment so it can be passed in when running recon-all.
RUN python -c 'import os, json; f = open("/tmp/gear_environ.json", "w"); json.dump(dict(os.environ), f)'

# Install a version of python to run Flywheel code and keep it separate from the
# python that Freesurfer uses.  Saving the environment above makes sure it is not
# changed in the Flyfwheel environment.

# Set CPATH for packages relying on compiled libs (e.g. indexed_gzip)
ENV PATH="/root/miniconda3/bin:$PATH" \
    CPATH="/root/miniconda3/include/:$CPATH" \
    LANG="C.UTF-8" \
    PYTHONNOUSERSITE=1

RUN wget \
    https://repo.anaconda.com/miniconda/Miniconda3-py38_4.8.3-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniconda3-py38_4.8.3-Linux-x86_64.sh -b \
    && rm -f Miniconda3-py38_4.8.3-Linux-x86_64.sh

# Installing precomputed python packages
RUN conda install -y python=3.8.5 && \
    chmod -R a+rX /root/miniconda3; sync && \
    chmod +x /root/miniconda3/bin/*; sync && \
    conda build purge-all; sync && \
    conda clean -tipsy && sync

COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/pip

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
WORKDIR ${FLYWHEEL}

# Copy executable/manifest to Gear
COPY manifest.json ${FLYWHEEL}/manifest.json
COPY run.py ${FLYWHEEL}/run.py

# Configure entrypoint
RUN chmod a+x ${FLYWHEEL}/run.py
ENTRYPOINT ["/flywheel/v0/run.py"]
