PROJECT=warre
REPO=registry.rc.nectar.org.au/nectar
SHA=$(shell git rev-parse --verify --short HEAD)
RELEASE=$(shell git rev-parse --abbrev-ref HEAD | tr '/' '-')
TAG_PREFIX=$(RELEASE)-
IMAGE_TAG := $(if $(TAG),$(TAG),$(TAG_PREFIX)$(SHA))
IMAGE=$(REPO)/$(PROJECT):$(IMAGE_TAG)
BUILDER=docker
BUILDER_ARGS=
build:
	$(BUILDER) build $(BUILDER_ARGS) -t $(IMAGE) .
push:
	$(BUILDER) push $(IMAGE)
.PHONY: build push
