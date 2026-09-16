FROM continuumio/miniconda3:latest

WORKDIR /app

COPY . /app

RUN conda config --add channels conda-forge && \
    conda config --add channels cadquery && \
    conda install -y python=3.10 cadquery=2.4 && \
    conda clean -afy

RUN pip install --no-cache-dir fastapi uvicorn google-genai

EXPOSE 8000

CMD ["python", "run_server.py"]