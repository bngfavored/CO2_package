FROM python:3.8

WORKDIR /usr/src/app

COPY requirements.txt ./
COPY docker_entrypoint.sh ./

RUN apt-get update
RUN apt-get install -y bluez bluetooth
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT sh docker_entrypoint.sh
