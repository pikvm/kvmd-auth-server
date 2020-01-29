-include config.mk

HTTP_HOST ?= localhost
HTTP_PORT ?= 8080

DB_HOST ?= localhost
DB_PORT ?= 3306
DB_USER ?=
DB_PASSWD ?=
DB_NAME ?= change_me
AUTH_QUERY ?= SELECT 1 FROM users WHERE user = %%(user)s AND passwd = %%(passwd)s AND secret = %%(secret)s

IMAGE ?= kvmd-auth-server


# =====
define optbool
$(filter $(shell echo $(1) | tr A-Z a-z),yes on 1)
endef


# =====
all:
	true


tox: build
	docker run --rm \
			--volume `pwd`:/root:ro \
			--volume `pwd`/deploy:/root/deploy:ro \
			--volume `pwd`/linters:/root/linters:rw \
		-it $(IMAGE) tox -q -c /root/linters/tox.ini $(if $(E),-e $(E),-p auto)


run: build
	docker run --rm \
			--net host \
			--env HTTP_HOST="$(HTTP_HOST)" \
			--env HTTP_PORT="$(HTTP_PORT)" \
			--env DB_HOST="$(DB_HOST)" \
			--env DB_PORT="$(DB_PORT)" \
			--env DB_USER="$(DB_USER)" \
			--env DB_PASSWD="$(DB_PASSWD)" \
			--env DB_NAME="$(DB_NAME)" \
			--env AUTH_QUERY="$(AUTH_QUERY)" \
		-it $(IMAGE) $(if $(CMD),$(CMD),/root/server.py)


build:
	docker build --rm $(if $(call optbool,$(NC)),--no-cache,) -t $(IMAGE) -f deploy/Dockerfile .


clean-all: build
	docker run --rm \
			--volume `pwd`:/root:rw \
		-it $(IMAGE) bash -c "rm -rf /root/linters/{.tox,.mypy_cache,.coverage}"
