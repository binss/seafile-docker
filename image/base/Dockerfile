# Lastet phusion baseimage as of 20180412, based on ubuntu 16.04
# See https://hub.docker.com/r/phusion/baseimage/tags/
FROM phusion/baseimage:0.10.1

ENV UPDATED_AT=20180412 \
    DEBIAN_FRONTEND=noninteractive

CMD ["/sbin/my_init", "--", "bash", "-l"]

RUN apt-get update -qq

# Utility tools
RUN apt-get install -qq -y vim net-tools psmisc wget curl

# Guidline for installing python libs: if a lib has C-compoment (e.g.
# python-imaging depends on libjpeg/libpng), we install it use apt-get.
# Otherwise we install it with pip.
RUN apt-get install -y python2.7-dev python-imaging python-ldap python-mysqldb
RUN curl -sSL -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py && \
    python /tmp/get-pip.py && \
    rm -rf /tmp/get-pip.py && \
    pip install -U wheel

ADD requirements.txt  /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /etc/my_init.d && rm -f /etc/my_init.d/00_regen_ssh_host_keys.sh

# Clean up for docker squash
# See https://github.com/goldmann/docker-squash
RUN rm -rf \
    /root/.cache \
    /root/.npm \
    /root/.pip \
    /usr/local/share/doc \
    /usr/share/doc \
    /usr/share/man \
    /usr/share/vim/vim74/doc \
    /usr/share/vim/vim74/lang \
    /usr/share/vim/vim74/spell/en* \
    /usr/share/vim/vim74/tutor \
    /var/lib/apt/lists/* \
    /tmp/*
