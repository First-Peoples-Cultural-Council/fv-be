ARG python_image=python:3.11.4-alpine
ARG caddy_image=caddy:2.6.4-alpine

FROM --platform=linux/arm64 python:3.11.4-alpine AS django-common
ENV DEBUG_DISABLE=True

WORKDIR /app
RUN apk add --no-cache build-base=0.5-r3
RUN apk add --no-cache libffi-dev
RUN apk add --no-cache libmagic
RUN apk add --no-cache openblas-dev
RUN apk add --no-cache ffmpeg
RUN apk add --no-cache git
RUN pip3 install gunicorn

COPY requirements.txt /app
RUN pip3 install -r requirements.txt

COPY . /app
WORKDIR /app/firstvoices

# intermediate stage to assemble static files for the caddy runtime stage
FROM --platform=linux/arm64 django-common AS static-collector
RUN ["python3", "manage.py", "collectstatic"]

# select with --target static-runtime at build time
FROM --platform=linux/arm64 $caddy_image AS static-runtime
COPY --from=static-collector /app/firstvoices/static /srv

# or django-runtime for the api server. this is last so that it's the default if no target specified
FROM --platform=linux/arm64 django-common AS django-runtime
EXPOSE 8000
CMD ["gunicorn", "--timeout", "120", "-b", "0.0.0.0:8000", "firstvoices.wsgi:application"]
