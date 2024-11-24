FROM python:3

COPY *.py .
COPY requirements.txt .
RUN python -m pip install -r requirements.txt
RUN python 01-download-model.py
