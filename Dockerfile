FROM python:3.6

WORKDIR /musicscan

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY musicscan ./musicscan
COPY musicscan-cli .

WORKDIR /musicscan/run

ENTRYPOINT [ "../musicscan-cli" ]
