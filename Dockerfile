FROM tercen/runtime-python39:0.1.0

RUN apt-get update && apt-get install -y \
    inkscape=0.92.4 \
    libreoffice=6.1.5.2

COPY . /operator
WORKDIR /operator

ENV PYTHONPATH "${PYTHONPATH}:~/.pyenv/versions/3.9.0/bin/python3"
RUN python3 -m pip install -r ./requirements.txt




ENV TERCEN_SERVICE_URI https://tercen.com

ENTRYPOINT [ "python3", "main.py"]
CMD [ "--taskId", "someid", "--serviceUri", "https://tercen.com", "--token", "sometoken"]
