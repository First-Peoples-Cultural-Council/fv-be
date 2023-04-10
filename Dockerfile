FROM python:3.11.2-alpine

EXPOSE 8000
WORKDIR /app
RUN pip3 install gunicorn

COPY requirements.txt /app
RUN pip3 install -r requirements.txt

COPY . /app

WORKDIR /app/firstvoices
CMD ["gunicorn"  , "-b", "0.0.0.0:8000", "firstvoices.wsgi:application"]

