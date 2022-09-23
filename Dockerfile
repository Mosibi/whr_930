FROM python:3

WORKDIR /usr/src/app

COPY ./src/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src/config.yaml .
COPY ./src/whr930.py .

CMD ["python", "./whr930.py"]
