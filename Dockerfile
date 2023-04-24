FROM python:3.11.2-alpine
ENV DEBUG_DISABLE=True

EXPOSE 8000
WORKDIR /app
RUN apk add build-base
RUN apk add libffi-dev
RUN pip3 install gunicorn

COPY requirements.txt /app
RUN pip3 install -r requirements.txt

COPY . /app

WORKDIR /app/firstvoices
RUN ["python3", "manage.py", "collectstatic"]
CMD ["gunicorn"  , "-b", "0.0.0.0:8000", "firstvoices.wsgi:application"]

