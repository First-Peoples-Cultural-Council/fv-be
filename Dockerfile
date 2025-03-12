ARG python_image=python:3.12.7-alpine
ARG caddy_image=caddy:2.7.6-alpine

FROM $python_image AS django-common
ENV DEBUG_DISABLE=True

WORKDIR /app
# Switch APK to use the Edge repository instead of v3.20 (Temporary until 3.20 has non vulnerable packages)
RUN echo "https://dl-cdn.alpinelinux.org/alpine/edge/main" > /etc/apk/repositories \
    && echo "https://dl-cdn.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories \
    && apk update

# Now you can proceed with upgrading all packages
RUN apk upgrade
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
