.PHONY: build update upgrade setup start stop restart status

all:
	@echo "Control the docker compose server"
	@echo "Usage: make [build/update/upgrade/setup/start/stop/restart/status]"
	@exit 0

build:
	docker-compose build

update:
	docker-compose up -d --build

upgrade:
	docker-compose up -d --build
	docker-compose run app upgrade

setup: start
	docker-compose run app setup

start:
	docker-compose up -d

stop:
	docker-compose down

restart: stop start

status:
	docker-compose ps
