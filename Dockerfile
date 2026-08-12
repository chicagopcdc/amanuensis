# To build: docker build -t amanuensis:latest .
# To run interactive:
#   docker run -v ~/.gen3/amanuensis/amanuensis-config.yaml:/var/www/amanuensis/amanuensis-config.yaml  amanuensis:latest
# To check running container do: docker exec -it CONTAINER bash

ARG AZLINUX_BASE_VERSION=3.13-pythonnginx


# ------ Base stage ------
FROM quay.io/cdis/amazonlinux-base:${AZLINUX_BASE_VERSION} AS base
# Comment this in, and comment out the line above, if quay is down
# FROM 707767160287.dkr.ecr.us-east-1.amazonaws.com/gen3/python-nginx-al:${AZLINUX_BASE_VERSION} as base

ENV appname=amanuensis

WORKDIR /${appname}
USER root
RUN chown -R gen3:gen3 /${appname}
RUN chown -R gen3:gen3 /venv
USER gen3

# ------ Builder stage ------
FROM base AS builder

ENV POETRY_VIRTUALENVS_CREATE=false

# copy ONLY poetry artifact, install the dependencies but not the app;
# this will make sure that the dependencies are cached
COPY poetry.lock pyproject.toml /${appname}/
WORKDIR /${appname}
RUN poetry install -vv --no-root --only main --no-interaction

# Move app files into working directory
COPY --chown=gen3:gen3 . /$appname
COPY --chown=gen3:gen3 ./deployment/wsgi/wsgi.py /$appname/wsgi.py

# install the app
RUN poetry install --without dev --no-interaction

# Setup version info
# RUN git config --global --add safe.directory ${appname} && COMMIT=`git rev-parse HEAD` && echo "COMMIT=\"${COMMIT}\"" > $appname/version_data.py \
#     && VERSION=`git describe --always --tags` && echo "VERSION=\"${VERSION}\"" >> $appname/version_data.py

# ------ Final stage ------
FROM base

COPY --chown=gen3:gen3 --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

USER root
# Install ccrypt to decrypt dbgap telmetry files
RUN echo "Upgrading dnf"; \
    dnf upgrade -y; \
    echo "Installing Packages"; \
    dnf install -y \
        libxcrypt-compat-4.4.33 \
        libpq-15.0 \
        gcc \
        diffutils \
        tar xz; \
    echo "Installing RPM"; \
    rpm -i https://ccrypt.sourceforge.net/download/1.11/ccrypt-1.11-1.src.rpm && \
    cd /root/rpmbuild/SOURCES/ && \
    tar -zxf ccrypt-1.11.tar.gz && cd ccrypt-1.11 && ./configure --disable-libcrypt && make install && make check;

COPY --chown=gen3:gen3 --from=builder /$appname /$appname
RUN mkdir -p /var/www/amanuensis && \
    chown -R gen3:gen3 /var/www/amanuensis

USER gen3

CMD ["/bin/bash", "-c", "/amanuensis/dockerrun.bash"]
