#FROM tercen/runtime-python39:0.2.2

#FROM debian:bookworm-slim
FROM ubuntu:jammy

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y build-essential \
	ca-certificates \
	sudo \
	git \
	jq \
	libbz2-dev \
	libffi-dev \
	libreadline-dev \
	libssl-dev \
	libsqlite3-dev \
	liblzma-dev \
	zlib1g-dev \
	wget \
	curl \
	llvm \
	libncurses5-dev \
	libncursesw5-dev \
	xz-utils \
	tk-dev

RUN wget https://www.python.org/ftp/python/3.9.17/Python-3.9.17.tar.xz && \
	tar -xf Python-3.9.17.tar.xz && \
	cd Python-3.9.17 && \
	./configure && \
	make && \
	sudo make install && \
	alias python=python3.9

RUN pip3 install wheel


RUN apt-get install -y software-properties-common python3-launchpadlib

RUN add-apt-repository ppa:inkscape.dev/stable-1.2
RUN apt-get update && apt-get install -y inkscape libreoffice



COPY . /operator
COPY ./config/inkscape_preferences.xml /home/root/.config/inkscape/preferences.xml
WORKDIR /operator

ENV PYTHONPATH "${PYTHONPATH}:~/.pyenv/versions/3.9.0/bin/python3"
ENV PATH "${PATH}:~/.pyenv/versions/3.9.0/bin/python3"
RUN python3 -m pip install -r ./requirements.txt

ENV TERCEN_SERVICE_URI https://tercen.com
ENV HOME /home/root
ENV OPENBLAS_NUM_THREADS="1"
ENV MKL_NUM_THREADS="1"


ENTRYPOINT [ "python3", "main.py"]
CMD [ "--taskId", "someid", "--serviceUri", "https://tercen.com", "--token", "sometoken"]
