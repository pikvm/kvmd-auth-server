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
		-t $(IMAGE) tox -q -c /root/linters/tox.ini $(if $(E),-e $(E),-p auto)


run: build
	docker run --rm \
			--net host \
			--volume `pwd`/config.yaml:/root/config.yaml:ro \
		-t $(IMAGE) $(if $(CMD),$(CMD),/root/server.py --config /root/config.yaml)


build:
	docker build --rm $(if $(call optbool,$(NC)),--no-cache,) -t $(IMAGE) -f deploy/Dockerfile .


clean-all: build
	docker run --rm \
			--volume `pwd`:/root:rw \
		-t $(IMAGE) bash -c "rm -rf /root/linters/{.tox,.mypy_cache,.coverage}"
