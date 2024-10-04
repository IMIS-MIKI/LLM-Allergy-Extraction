FROM continuumio/miniconda3

WORKDIR /app

RUN mkdir -p logs
COPY environment.yml environment.yml
RUN conda env create -f environment.yml
RUN echo "conda activate allergy-extraction" >> ~/.bashrc
COPY *.py /app
COPY entrypoint.sh entrypoint.sh
RUN chmod -R +x /app/entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
