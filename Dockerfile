FROM tercen/runtime-python39:0.1.0

COPY . /operator
WORKDIR /operator

#"imagemagick && sudo apt-get -y install inkscape && sudo apt-get -y install libreoffice"

ENV PYTHONPATH "${PYTHONPATH}:~/.pyenv/versions/3.9.0/bin/python3"
RUN python3 -m pip install -r ./requirements.txt

RUN apt-get update && apt-get install -y \
    imagemagick \
    inkscape \
    libreoffice


ENV TERCEN_SERVICE_URI https://tercen.com

ENTRYPOINT [ "python3", "main.py"]
CMD [ "--taskId", "someid", "--serviceUri", "https://tercen.com", "--token", "sometoken"]
