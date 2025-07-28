ARG python_image=python:3.13.5-alpine3.22
ARG caddy_image=caddy:2.10.0-alpine

FROM $python_image AS django-common
ENV DEBUG_DISABLE=True

WORKDIR /app
RUN apk add --no-cache \
    build-base \
    ffmpeg \
    git \
    libffi-dev \
    libmagic \
    openblas-dev
RUN pip3 install gunicorn
RUN pip3 install pipdeptree

COPY requirements.txt /app
RUN pip3 install -r requirements.txt

COPY . /app
WORKDIR /app/firstvoices

# intermediate stage to assemble static files for the caddy runtime stage
FROM django-common AS static-collector
RUN ["python3", "manage.py", "collectstatic"]

# select with --target static-runtime at build time
FROM $caddy_image AS static-runtime
COPY --from=django-common /app/Caddyfile /etc/caddy
COPY --from=static-collector /app/firstvoices/static /srv

# or django-runtime for the api server. this is last so that it's the default if no target specified
FROM django-common AS django-runtime
EXPOSE 8000
CMD ["gunicorn", "--timeout", "120", "-b", "0.0.0.0:8000", "firstvoices.wsgi:application"]
