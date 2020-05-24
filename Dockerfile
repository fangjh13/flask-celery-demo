FROM python:3.8.2

RUN useradd -m box
USER box

WORKDIR /home/box

ENV FLASK_APP=service.py
ENV FLASK_ENV=development

COPY requirements.txt .
RUN python -m venv venv
RUN venv/bin/pip install --no-cache-dir -r requirements.txt

COPY app app
COPY config.py service.py ./
COPY run.sh run.sh

EXPOSE 5000
CMD ["/bin/bash", "./run.sh", "flask"]
