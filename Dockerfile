#FROM tercen/runtime-python39:0.2.2

FROM debian:bullseye-backports
#FROM ubuntu:jammy

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

RUN apt-get install -y software-properties-common python3-launchpadlib cmake

RUN apt-get install -y libdouble-conversion-dev \
		libgdl-3-dev libagg-dev libpotrace-dev \
		libboost-all-dev libsoup2.4-dev libgc-dev \
		libwpg-dev poppler-utils libpoppler-dev \
		libpoppler-glib-dev libpoppler-private-dev \
		libvisio-dev libvisio-tools libcdr-dev \
		libgtkmm-3.0-dev libgspell-1-dev libxslt-dev \
		libreadline-dev 

RUN apt-get install -y lib2geom-dev
COPY ./dep/inkscape-1.1.x.tar.gz /home/root/inkscape/inkscape-1.1.x.tar.gz

RUN echo ","
RUN cd /home/root/inkscape/ && tar -xvzf inkscape-1.1.x.tar.gz
RUN ls /home/root/inkscape/

RUN apt-get install -y  libgsl-dev
# RUN apt-get install -y ccache
# RUN cd /home/root/inkscape/inkscape-1.1.x && \
# 	mkdir build && \
# 	cd build && \
# 	cmake .. -DCMAKE_INSTALL_PREFIX=/home/root/inkscape_bin -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache && \
# 	make -j6 


RUN apt-get install -y ninja-build ccache
RUN cd /home/root/inkscape/inkscape-1.1.x  &&\
		ln -s /home/root/inkscape/inkscape-1.1.x/share ./share/inkscape &&\
		mkdir -p build/conf &&\
		cd build &&\
		export INKSCAPE_PROFILE_DIR=/home/root/inkscape/inkscape-1.1.x/build/conf &&\
		cmake -DCMAKE_INSTALL_PREFIX:PATH=/home/root/inkscape/inkscape-1.1.x -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache -DCMAKE_BUILD_TYPE=Debug -G Ninja .. &&\
		ninja

#/home/root/inkscape_bin/share/inkscape/ui/units.xml NOT FOUND
#subprocess.call(["inkscape", saveImgPath, "--export-extension=org.inkscape.output.emf", "-o", outImgPath])

#COPY test.svg /home/root/test.svg
RUN rm -rf /root/.config/inkscape
RUN mkdir -p /root/.config/inkscape
COPY ./config/inkscape_pref.zip /root/.config/inkscape/inkscape.zip
RUN apt-get install unzip
RUN sudo unzip /root/.config/inkscape/inkscape.zip -d /root/.config/inkscape/
RUN export INKSCAPE_PROFILE_DIR=/root/.config/inkscape


#RUN echo ""
RUN ls  /root/.config/inkscape

#RUN ls -la /home/root/inkscape/inkscape-1.1.x/share/inkscape

#COPY ./config/inkscape_preferences.xml /home/root/inkscape/inkscape-1.1.x/build/conf/preferences.xml

#ENTRYPOINT [ "/home/root/inkscape/inkscape-1.1.x/build/bin/inkscape"]
#CMD [ "-export-extension", "org.inkscape.output.emf"]

#RUN ./home/root/inkscape/inkscape-1.1.x/build/bin/inkscape /home/root/test.svg --export-extension=org.inkscape.output.emf -o /home/root/test2.emf
#RUN ls -la /home/root/
#RUN cd /home/root/inkscape/inkscape-1.1.x/ && cmake -L

#RUN ls /home/root/inkscape/inkscape-1.1.x


# continue installing inkscape from here

#RUN add-apt-repository ppa:inkscape.dev/stable-1.2

# RUN add-apt-repository ppa:inkscape.dev/stable-1.2
#RUN apt-get update

#RUN apt-cache policy inkscape
#RUN apt-get install -y software-properties-common python3-launchpadlib
#RUN add-apt-repository "deb http://archive.ubuntu.com/ubuntu/ focal main restricted universe multiverse"

#deb http://archive.ubuntu.com/ubuntu/ focal main restricted universe multiverse
#RUN apt-cache policy glibc-source 
#RUN apt-get install -y glibc-source=2.31-0ubuntu9

#RUN echo "11"

#RUN ldd --version

#RUN wget -c https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/glibc/2.31-0ubuntu9.14/glibc_2.31.orig.tar.xz
#RUN tar -xf glibc_2.31.orig.tar.xz 
#RUN ls 
#RUN cd glibc-2.31 && mkdir glibc-build && cd glibc-build && \
#	../configure --prefix=/opt/glibc-2.31
#RUN cd glibc-2.31/glibc-build && make -j4 && make install


# RUN apt-get install -y software-properties-common python3-launchpadlib

# RUN add-apt-repository ppa:inkscape.dev/stable-1.2
# RUN apt-get update && apt-get install -y inkscape libreoffice



COPY . /operator
#COPY ./config/inkscape_preferences.xml /home/root/.config/inkscape/preferences.xml
WORKDIR /operator

ENV PYTHONPATH "${PYTHONPATH}:~/.pyenv/versions/3.9.0/bin/python3"
ENV PATH "${PATH}:~/.pyenv/versions/3.9.0/bin/python3"
RUN python3 -m pip install -r ./requirements.txt

ENV TERCEN_SERVICE_URI https://tercen.com
#ENV HOME /home/root
#ENV OPENBLAS_NUM_THREADS="1"
#ENV MKL_NUM_THREADS="1"


ENTRYPOINT [ "python3", "main.py"]
CMD [ "--taskId", "someid", "--serviceUri", "https://tercen.com", "--token", "sometoken"]
