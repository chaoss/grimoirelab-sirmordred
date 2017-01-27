# Copyright (C) 2016 Bitergia
# GPLv3 License

FROM debian:8
MAINTAINER Luis Cañas-Díaz <lcanas@bitergia.com>

ENV DEBIAN_FRONTEND noninteractive
ENV DEPLOY_USER bitergia
ENV DEPLOY_USER_DIR /home/${DEPLOY_USER}
ENV SCRIPTS_DIR ${DEPLOY_USER_DIR}/scripts

# Initial user
RUN useradd bitergia --create-home --shell /bin/bash

# install dependencies
RUN apt-get update && \
    apt-get -y install --no-install-recommends \
        bash locales \
        git git-core \
        tree ccze \
        psmisc \
        python python3 pep8 \
        python3-dateutil python3-bs4 \
        python3-pip python3-dev python3-redis \
        python3-flask \
        python3-pandas \
        python-mysqldb \
        python3-cherrypy3 \
        python3-yaml \
        gcc make libmysqlclient-dev mariadb-client \
        unzip curl wget sudo ssh\
        && \
    apt-get clean && \
    find /var/lib/apt/lists -type f -delete

# Not available as package in Debian 8 python3-myssqldb
RUN pip3 install mysqlclient

# perceval needs a newer version than Debian 8 - this breaks pip3
RUN pip3 install requests

# solves issues with UNICODE and SH
RUN pip3 install sqlalchemy

# sortinghat needs pandas
# RUN pip3 install pandas # it crashes so we use the .deb

RUN echo "${DEPLOY_USER}    ALL=NOPASSWD: ALL" >> /etc/sudoers

RUN mkdir -p /home/bitergia/logs ; chown -R bitergia:bitergia /home/bitergia/logs
VOLUME ["/home/bitergia/logs"]

ADD stage ${DEPLOY_USER_DIR}/stage
RUN chmod 755 ${DEPLOY_USER_DIR}/stage

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    echo 'LANG="en_US.UTF-8"'>/etc/default/locale && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=en_US.UTF-8

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV LANG C.UTF-8

USER ${DEPLOY_USER}
WORKDIR ${DEPLOY_USER_DIR}

CMD ${DEPLOY_USER_DIR}/stage
