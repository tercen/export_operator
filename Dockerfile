#FROM tercen/runtime-python39:0.2.2
FROM debian:bookworm
# Using bookworm (Debian 12) which has lib2geom in main repository

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

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y libreoffice

# Extra libs for compiling Inkscape
RUN apt-get install -y software-properties-common python3-launchpadlib cmake \
		libdouble-conversion-dev \
		libgdl-3-dev libagg-dev libpotrace-dev \
		libboost-all-dev libsoup2.4-dev libgc-dev \
		libwpg-dev poppler-utils libpoppler-dev \
		libpoppler-glib-dev libpoppler-private-dev \
		libvisio-dev libvisio-tools libcdr-dev \
		libgtkmm-3.0-dev libgspell-1-dev libxslt-dev \
		libreadline-dev lib2geom-dev libgsl-dev \
		ninja-build ccache libcanberra-gtk-dev zip

# Copy inkscape source code
# COPY ./dep/inkscape-1.1.x.tar.gz /home/root/inkscape/inkscape-1.1.x.tar.gz
# RUN cd /home/root/inkscape/ && tar -xvzf inkscape-1.1.x.tar.gz

# # Build Inkscape
# RUN cd /home/root/inkscape/inkscape-1.1.x  &&\
# 		ln -s /home/root/inkscape/inkscape-1.1.x/share ./share/inkscape &&\
# 		mkdir -p build/conf &&\
# 		cd build &&\
# 		export INKSCAPE_PROFILE_DIR=/home/root/inkscape/inkscape-1.1.x/build/conf &&\
# 		cmake -DCMAKE_INSTALL_PREFIX:PATH=/home/root/inkscape/inkscape-1.1.x \
# 			  -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache -G Ninja .. &&\
		# ninja
RUN mkdir -p /home/root/inkscape/inkscape-1.3.2
COPY ./dep/inkscape-1.3.2.zip /home/root/inkscape/inkscape-1.3.2/inkscape-1.3.2.zip
RUN cd /home/root/inkscape/inkscape-1.3.2/ && unzip inkscape-1.3.2.zip && rm inkscape-1.3.2.zip



RUN ls /home/root/inkscape/ 
RUN ls /home/root/inkscape/inkscape-1.3.2/

# Build Inkscape
RUN cd /home/root/inkscape/inkscape-1.3.2  &&\
		ln -s /home/root/inkscape/inkscape-1.3.2/share ./share/inkscape &&\
		mkdir -p build/conf &&\
		cd build &&\
		export INKSCAPE_PROFILE_DIR=/home/root/inkscape/inkscape-1.3.2/build/conf &&\
		cmake -DCMAKE_INSTALL_PREFIX:PATH=/home/root/inkscape/inkscape-1.3.2 \
			  -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache -G Ninja .. &&\
		ninja


# Setup user profile, necessary to corretly point to the emf config in the preferences
RUN rm -rf /root/.config/inkscape
RUN mkdir -p /root/.config/inkscape
COPY ./config/inkscape_pref.zip /root/.config/inkscape/inkscape.zip
RUN apt-get install unzip
RUN sudo unzip /root/.config/inkscape/inkscape.zip -d /root/.config/inkscape/
RUN export INKSCAPE_PROFILE_DIR=/root/.config/inkscape

COPY . /operator
WORKDIR /operator

ENV PYTHONPATH "${PYTHONPATH}:~/.pyenv/versions/3.9.0/bin/python3"
ENV PATH "${PATH}:~/.pyenv/versions/3.9.0/bin/python3"
RUN python3 -m pip install -r ./requirements.txt

ENV TERCEN_SERVICE_URI https://tercen.com



ENTRYPOINT [ "python3", "main.py"]
# ENTRYPOINT [ "python3", "experimental.py"]
CMD [ "--taskId", "someid", "--serviceUri", "https://tercen.com", "--token", "sometoken"]
