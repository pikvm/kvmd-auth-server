FROM archlinux/archlinux:base
MAINTAINER Devaev Maxim <mdevaev@gmail.com>

RUN mkdir -p /etc/pacman.d/hooks \
	&& ln -s /dev/null /etc/pacman.d/hooks/30-systemd-tmpfiles.hook

RUN pacman --noconfirm -Syu \
	&& pacman --needed --noconfirm -S \
		git \
		python \
		python-pip \
		python-tox \
	&& (pacman --noconfirm -Sc || true) \
	&& rm -rf /var/cache/pacman/pkg/*

COPY deploy/requirements.txt /root/requirements.txt
RUN pip install -r /root/requirements.txt

COPY server.py /root/server.py

CMD /bin/bash
