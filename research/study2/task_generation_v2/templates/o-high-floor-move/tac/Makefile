PROFILE ?= R1
IMAGE = tac-study21-o-high-floor-move:v01-$(shell echo $(PROFILE) | tr A-Z a-z)
.PHONY: build
build:
	docker build --platform linux/amd64 --build-arg PROFILE=$(PROFILE) -t $(IMAGE) .
