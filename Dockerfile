FROM continuumio/miniconda3:latest

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglu1-mesa \
    libglib2.0-0 \
    libsm6 \
    libice6 \
    libxext6 \
    libxrender1 \
    libxcursor1 \
    libxft2 \
    libxinerama1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN conda config --add channels conda-forge && \
    conda config --add channels cadquery && \
    conda install -y python=3.10 cadquery=2.4 && \
    conda clean -afy

RUN pip install --no-cache-dir fastapi uvicorn google-genai

EXPOSE 8000

CMD ["python", "run_server.py"]