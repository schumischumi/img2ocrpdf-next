FROM python:3.10

WORKDIR /code

COPY ./requirements/requirements.txt /code/requirements.txt

RUN apt-get -y update && apt-get -y upgrade && apt -y install tesseract-ocr tesseract-ocr-deu

RUN /usr/local/bin/python -m pip install --upgrade pip 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN rm -rf /code/requirements.txt

COPY ./app /code

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080","--log-level","debug"]