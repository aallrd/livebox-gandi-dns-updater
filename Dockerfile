FROM python:3.7-slim

LABEL maintainer="aallrd"
LABEL version="1.0"
LABEL description="Update the DNS records for Gandi \
registered domains based on the current Livebox WAN address."
LABEL project="https://github.com/aallrd/livebox-gandi-dns-updater"

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT [ "./updater.py" ]