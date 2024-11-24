FROM python:3.12.7

COPY requirements.txt .

RUN pip install --upgrade pip

RUN python -m pip install -r requirements.txt

WORKDIR /app/src

COPY *.py /app/src
COPY prompts /app/src/prompts/
COPY python /app/src/python/
COPY web /app/src/web/
COPY .env /app/src

RUN ls -la

EXPOSE 8080

CMD ["python", "uiapp.py"] 
