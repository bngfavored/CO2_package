FROM hilschernetpi/netpi-bluetooth

WORKDIR /usr/src/app

COPY requirements.txt ./
COPY docker_entrypoint.sh ./

RUN apt-get update
RUN apt-get install -y
RUN apt-get install -y python3.8
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT sh docker_entrypoint.sh
