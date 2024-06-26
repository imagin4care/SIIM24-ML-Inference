FROM nvidia/cuda:11.7.1-cudnn8-runtime-ubuntu22.04

SHELL ["/bin/bash", "-l", "-c"]
WORKDIR /app
# Install essential packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    git \
    curl \
    ca-certificates \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libstdc++6 \
    unzip && \
    wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    /bin/bash /tmp/miniconda.sh -b -p /opt/conda && \
    rm /tmp/miniconda.sh && \
    rm -rf /var/lib/apt/lists/*

ENV PATH=/opt/conda/bin:$PATH

ENV HOLOSCAN_INPUT_PATH=dcm
ENV HOLOSCAN_MODEL_PATH=models
ENV HOLOSCAN_OUTPUT_PATH=output
COPY monai_env.yml /app/monai_env.yml
RUN conda env create -f monai_env.yml && \
    echo "source activate monai_env" > ~/.bashrc && \
    conda install pytorch torchvision torchaudio cudatoolkit=11.3 -c pytorch && \
    ln -sf /usr/lib/x86_64-linux-gnu/libstdc++.so.6 /opt/conda/envs/monai_env/lib/python3.10/site-packages/../../libstdc++.so.6 && \
    conda clean -afy

COPY app /app

ENV PATH /opt/conda/envs/monai_env/bin:$PATH
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
#CMD ["python", "-m", "app"]