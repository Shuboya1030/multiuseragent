IMAGE_NAME=must-securescan-purchase-image
CONTAINER_NAME=must-securescan-purchase

.PHONY: build run stop
build:
	docker build -t $(IMAGE_NAME) .
run:
	docker run --network host --name $(CONTAINER_NAME) -it $(IMAGE_NAME) /bin/bash
stop:
	docker stop $(CONTAINER_NAME)
	docker rm $(CONTAINER_NAME)
