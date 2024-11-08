FROM continuumio/miniconda3

WORKDIR /app

RUN mkdir -p logs
RUN mkdir -p src
RUN mkdir -p codes

COPY environment.yml environment.yml
RUN conda env create -f environment.yml
RUN echo "conda activate allergy-extraction" >> ~/.bashrc

COPY *.py /app
COPY src/* /app/src/
COPY entrypoint.sh entrypoint.sh

RUN chmod -R +x /app/entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
