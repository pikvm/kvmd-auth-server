FROM archlinux/base
MAINTAINER Devaev Maxim <mdevaev@gmail.com>

RUN pacman --noconfirm -Syy \
	&& pacman --needed --noconfirm -S \
		glibc \
		pacman \
	&& pacman-db-upgrade \
	&& pacman --noconfirm -Syu \
	&& pacman --needed --noconfirm -S \
		p11-kit \
		archlinux-keyring \
		ca-certificates \
		ca-certificates-mozilla \
		ca-certificates-utils \
	&& pacman --needed --noconfirm -S \
		git \
		python \
		python-pip \
		python-tox \
	&& (pacman --noconfirm -Sc || true)

COPY deploy/requirements.txt /root/requirements.txt
RUN pip install -r /root/requirements.txt

COPY server.py /root/server.py

CMD /root/server.py \
	--http-port "$HTTP_HOST" \
	--http-port "$HTTP_PORT" \
	--db-host "$DB_HOST" \
	--db-port "$DB_PORT" \
	--db-user "$DB_USER" \
	--db-passwd "$DB_PASSWD" \
	--db-name "$DB_NAME" \
	--auth-query "$AUTH_QUERY"
